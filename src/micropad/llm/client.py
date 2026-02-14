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


# OpenAI Pricing (in USD per 1M tokens)
# ============================================================================
# IMPORTANT: OpenAI does NOT provide pricing via API - must be manually updated
#
# Last Updated: January 2025
# Source: https://openai.com/api/pricing/
#
# To update pricing:
#   1. Visit https://openai.com/api/pricing/
#   2. Update values below (input/output per 1M tokens)
#   3. Update "Last Updated" date above
#   4. Pricing changes are announced at https://openai.com/blog
# ============================================================================
OPENAI_PRICING = {
    "gpt-5-nano-2025-08-07": {"input": 0.05, "output": 0.40}
}


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
        Calculate cost for OpenAI API call.

        Args:
            model: Model name (e.g., "gpt-4o", "gpt-4o-mini")
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens

        Returns:
            Cost in USD
        """
        # Normalize model name (handle versioned names)
        model_key = model
        if model not in OPENAI_PRICING:
            # Try to find base model
            for base_model in OPENAI_PRICING.keys():
                if model.startswith(base_model):
                    model_key = base_model
                    break

        if model_key not in OPENAI_PRICING:
            # Unknown model - return 0 and log warning
            logging.getLogger("events").warning(
                f"Unknown model pricing for '{model}' - cost will be $0.00"
            )
            return 0.0

        pricing = OPENAI_PRICING[model_key]
        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]

        return input_cost + output_cost


class LLMClient:
    """Centralized LLM calling with provider abstraction."""

    def __init__(self):
        self.provider = config.AI_PROVIDER
        self.events_log = logging.getLogger("events")
        self.conv_log = logging.getLogger("conversations")

        # ✅ NEW: Token usage tracker
        self.token_usage = TokenUsage()

        if self.provider == "openai":
            self._init_openai()

    def print_cost_summary(self):
        """Print and log comprehensive cost summary."""
        summary = self.token_usage.get_summary()

        print("\n" + "=" * 80)
        print("API COST SUMMARY")
        print("=" * 80)

        print(f"\nTotal Tokens: {summary['total_tokens']:,}")
        print(f"  Input:  {summary['total_input_tokens']:,}")
        print(f"  Output: {summary['total_output_tokens']:,}")

        if summary['total_cost_usd'] > 0:
            print(f"\nTotal Cost: ${summary['total_cost_usd']:.4f} USD")
        else:
            print(f"\nTotal Cost: $0.00 USD (using local model)")

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
        Call configured LLM provider.

        Returns:
            dict with keys: 'content' (str), 'metadata' (dict)
        """
        provider = config.AI_PROVIDER.lower()

        if provider == "ollama":
            return self._call_ollama(system_prompt, user_prompt, operation)
        elif provider == "openai":
            return self._call_openai(system_prompt, user_prompt, operation)
        else:
            raise ValueError(f"Unsupported LLM provider: {config.AI_PROVIDER}")

    def _init_openai(self):
        if not config.OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY required")
        from openai import OpenAI

        self.openai_client = OpenAI(api_key=config.OPENAI_API_KEY, base_url=config.OPENAI_BASE_URL)

    def call(
        self, model: str, system_prompt: str, user_prompt: str, operation: str = "llm_call"
    ) -> str:
        """Unified LLM call with automatic provider routing and token tracking."""
        if self.provider == "openai":
            return self._call_openai(model, system_prompt, user_prompt, operation)
        else:
            return self._call_ollama(model, system_prompt, user_prompt, operation)

    def _build_request_kwargs(self, model: str, system: str, user: str, send_temp: bool) -> dict:
        """Build request kwargs for OpenAI API."""
        kwargs = {
            "model": model,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        }
        if send_temp and config.TEMPERATURE is not None:
            kwargs["temperature"] = config.TEMPERATURE
        return kwargs

    def _is_temperature_error(self, e: Exception) -> bool:
        """Check if error is temperature-related."""
        err_str = str(e).lower()
        return "unsupported_value" in err_str or "temperature" in err_str

    def _call_openai(
        self, system_prompt: str, user_prompt: str, operation: str, max_retries: int = 3
    ) -> dict:
        """
        Call OpenAI API with retry logic.

        Returns:
            dict with keys: 'content' (str), 'metadata' (dict)
        """
        from openai import OpenAI

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

        client = OpenAI(api_key=config.OPENAI_API_KEY)

        for attempt in range(max_retries):
            try:
                self._log_request(run_id, "openai", model, system_prompt, user_prompt, True)

                # Build request arguments dynamically
                request_kwargs = {
                    "model": model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    # Note: The correct parameter name for v1+ of the OpenAI client is 'max_tokens'
                    "max_completion_tokens": config.MAX_TOKENS,
                }

                # Only add temperature if it is not None
                if config.TEMPERATURE is not None:
                    request_kwargs["temperature"] = config.TEMPERATURE

                # Make the call with the conditional arguments
                response = client.chat.completions.create(**request_kwargs)

                content = response.choices[0].message.content

                # Extract token usage
                input_tokens = response.usage.prompt_tokens
                output_tokens = response.usage.completion_tokens
                total_tokens = response.usage.total_tokens

                # Calculate cost
                actual_model = response.model  # Use actual model returned by API for pricing
                cost_usd = TokenUsage.calculate_cost(actual_model, input_tokens, output_tokens)

                # Record usage and cost
                self.token_usage.record(operation, input_tokens, output_tokens, cost_usd)

                # Log response with cost
                self._log_response(run_id, "openai", model, response, cost_usd)

                # Log per-call cost to events log
                self.events_log.info(
                    f"[{operation}] OpenAI API call: {input_tokens} in + {output_tokens} out = "
                    f"{total_tokens} tokens | Cost: ${cost_usd:.4f}"
                )

                # NEW: Build and return metadata
                metadata = {
                    "provider": "openai",
                    "model": model,
                    "model_version": actual_model,  # Actual version returned by API
                    "run_id": run_id,
                    "timestamp": datetime.now().isoformat(),
                    "operation": operation,
                    "tokens": {
                        "input": input_tokens,
                        "output": output_tokens,
                        "total": total_tokens,
                    },
                    "cost_usd": round(cost_usd, 6),
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

                if not is_retryable or attempt == max_retries - 1:
                    self._log_error(run_id, "openai", model, e)
                    raise RuntimeError(
                        f"OpenAI call failed after {attempt + 1} attempts: {str(e)[:100]}"
                    )

                base_delay = 2**attempt
                jitter = random.uniform(0, 0.1 * base_delay)
                wait_time = base_delay + jitter

                self.events_log.warning(
                    f"OpenAI call failed (attempt {attempt + 1}/{max_retries}), "
                    f"retrying in {wait_time:.1f}s: {str(e)[:100]}"
                )

                time.sleep(wait_time)

        raise RuntimeError(f"OpenAI call failed after {max_retries} retries")

    def _openai_request(self, model: str, system: str, user: str, send_temp: bool):
        """Make OpenAI API request."""
        kwargs = {
            "model": model,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        }
        if send_temp and config.TEMPERATURE is not None:
            kwargs["temperature"] = config.TEMPERATURE
        return self.openai_client.chat.completions.create(**kwargs)

    def _call_ollama(
        self, system_prompt: str, user_prompt: str, operation: str, max_retries: int = 3
    ) -> dict:
        """
        Call Ollama API with retry logic.

        Returns:
            dict with keys: 'content' (str), 'metadata' (dict)
        """
        import ollama

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

        for attempt in range(max_retries):
            try:
                self._log_request(run_id, "ollama", model, system_prompt, user_prompt, False)

                response = ollama.chat(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    options={"num_ctx": config.MAX_CONTEXT_LENGTH, "cache_prompt": True},
                )

                content = response["message"]["content"]

                # Estimate tokens (Ollama doesn't provide exact counts)
                estimated_input = (len(system_prompt) + len(user_prompt)) // 4
                estimated_output = len(content) // 4

                # Ollama is free (local model)
                cost_usd = 0.0

                self.token_usage.record(operation, estimated_input, estimated_output, cost_usd)
                self._log_response(run_id, "ollama", model, response, cost_usd)

                # NEW: Build and return metadata
                metadata = {
                    "provider": "ollama",
                    "model": model,
                    "run_id": run_id,
                    "timestamp": datetime.now().isoformat(),
                    "operation": operation,
                    "tokens": {
                        "input": estimated_input,
                        "output": estimated_output,
                        "total": estimated_input + estimated_output,
                    },
                    "note": "Token counts are estimated",
                }

                return {"content": content, "metadata": metadata}

            except Exception as e:
                error_str = str(e).lower()

                is_retryable = any(
                    x in error_str
                    for x in [
                        "timeout",
                        "connection",
                        "overloaded",
                        "busy",
                        "cuda",
                        "out of memory",
                        "try again",
                    ]
                )

                if not is_retryable or attempt == max_retries - 1:
                    self._log_error(run_id, "ollama", model, e)
                    raise RuntimeError(
                        f"Ollama call failed after {attempt + 1} attempts: {str(e)[:100]}"
                    )

                base_delay = 2**attempt
                jitter = random.uniform(0, 0.1 * base_delay)
                wait_time = base_delay + jitter

                self.events_log.warning(
                    f"Ollama call failed (attempt {attempt + 1}/{max_retries}), "
                    f"retrying in {wait_time:.1f}s: {str(e)[:100]}"
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
