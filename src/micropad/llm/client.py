import logging
import random
import time
import traceback
from datetime import datetime

from micropad.config import settings as config
from micropad.logging.manager import generate_run_id

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

# ============================================================================
# FULL CONVERSATION LOGGING ENABLED
# ============================================================================
# WARNING: This configuration logs COMPLETE LLM conversations including:
#   - Full system prompts (can be 5,000+ characters)
#   - Full user prompts (can be 10,000+ characters with full file contents)
#   - Full LLM responses (can be 2,000+ characters)
#
# Expected log file sizes:
#   - Small repo (50 files, 3 patterns): ~5-10 MB
#   - Medium repo (150 files, 5 patterns): ~20-50 MB
#   - Large repo (500 files, 10 patterns): ~100-200 MB
#
# Benefits:
#   ✓ Complete reproducibility
#   ✓ Full debugging capability
#   ✓ Prompt engineering analysis
#   ✓ Response quality verification
# ============================================================================


class TokenUsage:
    """Track token usage and costs across LLM calls."""

    def __init__(self):
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_cost = 0.0
        self.calls_by_operation = {}  # operation -> {input, output, cost, count}

    def record(self, operation: str, input_tokens: int, output_tokens: int, cost: float = 0.0):
        """Record token usage and cost for an operation."""
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        self.total_cost += cost

        if operation not in self.calls_by_operation:
            self.calls_by_operation[operation] = {"input": 0, "output": 0, "cost": 0.0, "count": 0}

        self.calls_by_operation[operation]["input"] += input_tokens
        self.calls_by_operation[operation]["output"] += output_tokens
        self.calls_by_operation[operation]["cost"] += cost
        self.calls_by_operation[operation]["count"] += 1

    def get_summary(self) -> dict:
        """Get token usage and cost summary."""
        return {
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_tokens": self.total_input_tokens + self.total_output_tokens,
            "total_cost_usd": round(self.total_cost, 4),
            "by_operation": self.calls_by_operation,
        }

    @staticmethod
    def calculate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
        """
        Calculate cost for an Ollama Cloud API call.

        Ollama Cloud is a flat subscription rather than per-token billing,
        so there is no meaningful per-call dollar cost to compute.
        """
        return 0.0


class LLMClient:
    """Centralized LLM calling with provider abstraction."""

    def __init__(self):
        self.events_log = logging.getLogger("events")
        self.conv_log = logging.getLogger("conversations")

        self.token_usage = TokenUsage()

        self._init_openai()

    def print_cost_summary(self):
        """Print and log comprehensive cost summary."""
        summary = self.token_usage.get_summary()

        print("\n" + "=" * 80)
        print("TOKEN USAGE SUMMARY")
        print("=" * 80)

        print(f"\nTotal Tokens: {summary['total_tokens']:,}")
        print(f"  Input:  {summary['total_input_tokens']:,}")
        print(f"  Output: {summary['total_output_tokens']:,}")

        if summary['by_operation']:
            print("\nBreakdown by Operation:")
            print("-" * 80)
            for operation, stats in sorted(summary['by_operation'].items()):
                count = stats['count']
                tokens = stats['input'] + stats['output']
                cost = stats.get('cost', 0.0)

                print(f"  {operation:<20} | Calls: {count:3d} | Tokens: {tokens:8,} | "
                      f"Cost: ${cost:7.4f}")

        print("=" * 80)

        # Also log to events
        self.events_log.info(
            f"Total API cost: ${summary['total_cost_usd']:.4f} | "
            f"Tokens: {summary['total_tokens']:,} | "
            f"Calls: {sum(s['count'] for s in summary['by_operation'].values())}"
        )

        return summary

    def call_llm(self, system_prompt: str, user_prompt: str, operation: str) -> dict:
        """
        Call Ollama Cloud.

        Returns:
            dict with keys: 'content' (str), 'metadata' (dict)
        """
        return self._call_ollama(system_prompt, user_prompt, operation)

    def _init_openai(self):
        if not config.OLLAMA_API_KEY:
            raise RuntimeError("OLLAMA_API_KEY required")
        from openai import OpenAI

        self.openai_client = OpenAI(api_key=config.OLLAMA_API_KEY, base_url=config.OLLAMA_BASE_URL)

    # Retryable errors are retried indefinitely (capped backoff, no giving
    # up) rather than a bounded number of attempts - the provider is
    # expected to eventually recover, and giving up early either crashes
    # the whole scan (planning/judge calls) or silently reports "no
    # evidence" (investigation calls) - both worse than waiting.
    MAX_RETRY_WAIT_SECONDS = 60

    def _call_ollama(
        self, system_prompt: str, user_prompt: str, operation: str
    ) -> dict:
        """
        Call Ollama Cloud via its OpenAI-compatible endpoint.

        Retryable errors (rate limits, timeouts, connection issues, 5xx) are
        retried indefinitely with a capped exponential backoff. Non-retryable
        errors (e.g. malformed requests) fail immediately - retrying those
        would never help.

        Returns:
            dict with keys: 'content' (str), 'metadata' (dict)
        """
        run_id = generate_run_id()

        # Determine which model to use based on operation
        if operation == "investigation":
            model = config.INVESTIGATOR_MODEL
        elif operation == "planning":
            model = config.PLANNER_MODEL
        elif operation == "deliberation":
            model = config.JUDGE_MODEL
        else:
            model = config.INVESTIGATOR_MODEL  # default

        attempt = 0
        while True:
            attempt += 1
            try:
                self._log_request(run_id, "ollama", model, system_prompt, user_prompt, True)

                request_kwargs = {
                    "model": model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "max_tokens": config.MAX_TOKENS,
                }

                if config.TEMPERATURE is not None:
                    request_kwargs["temperature"] = config.TEMPERATURE

                if config.REASONING_EFFORT:
                    request_kwargs["reasoning_effort"] = config.REASONING_EFFORT

                response = self.openai_client.chat.completions.create(**request_kwargs)

                content = response.choices[0].message.content

                # Extract token usage
                input_tokens = response.usage.prompt_tokens
                output_tokens = response.usage.completion_tokens
                total_tokens = response.usage.total_tokens

                cost_usd = 0.0  # Ollama Cloud is a flat subscription, not per-token billed

                self.token_usage.record(operation, input_tokens, output_tokens, cost_usd)
                self._log_response(run_id, "ollama", model, response, cost_usd)

                self.events_log.info(
                    f"[{operation}] Ollama Cloud API call: {input_tokens} in + {output_tokens} out = "
                    f"{total_tokens} tokens"
                )

                metadata = {
                    "provider": "ollama",
                    "model": model,
                    "model_version": response.model,  # Actual version returned by API
                    "run_id": run_id,
                    "timestamp": datetime.now().isoformat(),
                    "operation": operation,
                    "tokens": {
                        "input": input_tokens,
                        "output": output_tokens,
                        "total": total_tokens,
                    },
                    "cost_usd": 0.0,
                    "finish_reason": response.choices[0].finish_reason,
                }

                return {"content": content, "metadata": metadata}

            except Exception as e:
                error_str = str(e).lower()

                is_retryable = any(
                    x in error_str
                    for x in [
                        "rate limit",
                        "timeout",
                        "connection",
                        "overloaded",
                        "429",
                        "503",
                        "500",
                    ]
                )

                if not is_retryable:
                    self._log_error(run_id, "ollama", model, e)
                    raise RuntimeError(
                        f"Ollama Cloud call failed (non-retryable): {str(e)[:200]}"
                    )

                # Capped exponential backoff: grows up to MAX_RETRY_WAIT_SECONDS,
                # then holds there - we keep retrying rather than giving up.
                wait_time = min(2 ** min(attempt, 10), self.MAX_RETRY_WAIT_SECONDS)
                wait_time += random.uniform(0, 0.1 * wait_time)

                if attempt == 1 or attempt % 5 == 0:
                    self.events_log.warning(
                        f"Ollama Cloud call failed (attempt {attempt}), still retrying "
                        f"(waiting {wait_time:.0f}s): {str(e)[:150]}"
                    )

                time.sleep(wait_time)

    def _log_request(
        self, run_id: str, provider: str, model: str, system: str, user: str, send_temp: bool
    ):
        """Log LLM request with FULL prompts (no truncation)."""
        self.conv_log.info(
            "LLM Request",
            extra={
                "conversation_data": {
                    "run_id": run_id,
                    "provider": provider,
                    "model": model,
                    "temp_attempt": send_temp and config.TEMPERATURE,
                    "system_prompt": system,  # FULL prompt (no truncation)
                    "user_prompt": user,      # FULL prompt (no truncation)
                    "system_prompt_length": len(system),
                    "user_prompt_length": len(user),
                }
            },
        )

    def _log_response(self, run_id: str, provider: str, model: str, response, cost_usd: float = 0.0):
        """Log LLM response with FULL content and cost."""
        usage_info = {}
        response_content = None

        # Extract response content based on provider
        if provider == "openai" and hasattr(response, "usage"):
            usage = response.usage
            usage_info = {
                "prompt": getattr(usage, "prompt_tokens", None),
                "completion": getattr(usage, "completion_tokens", None),
                "total": getattr(usage, "total_tokens", None),
                "cost_usd": round(cost_usd, 6),
            }
            # Extract actual response content
            if hasattr(response, "choices") and len(response.choices) > 0:
                response_content = response.choices[0].message.content

        elif provider == "ollama":
            # For Ollama responses
            if isinstance(response, dict):
                response_content = response.get("message", {}).get("content", "")
                # Estimate tokens for logging
                estimated_tokens = len(response_content) // 4
                usage_info = {
                    "estimated_tokens": estimated_tokens,
                    "cost_usd": 0.0,
                    "note": "Ollama is free (local)",
                }

        self.conv_log.info(
            "LLM Response",
            extra={
                "conversation_data": {
                    "run_id": run_id,
                    "provider": provider,
                    "model": model,
                    "success": True,
                    "response_content": response_content,  # FULL response content
                    "response_length": len(response_content) if response_content else 0,
                    "tokens": usage_info if usage_info else None,
                }
            },
        )

    def _log_error(self, run_id: str, provider: str, model: str, error: Exception):
        """Log LLM error."""
        self.conv_log.error(
            "LLM Error",
            extra={
                "conversation_data": {
                    "run_id": run_id,
                    "provider": provider,
                    "model": model,
                    "error_type": type(error).__name__,
                    "error": str(error),
                    "traceback": traceback.format_exc(),
                }
            },
        )
