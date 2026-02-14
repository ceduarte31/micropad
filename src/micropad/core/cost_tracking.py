"""
Cost Tracking Module for LLM API Usage.

This module tracks token usage and calculates costs for different LLM providers
(OpenAI, Ollama, etc.) used throughout the pattern detection pipeline.

Classes:
    CostTracker: Tracks and calculates LLM API costs based on token usage.
"""

from typing import Dict, Optional

from micropad.logging.ui import Colors

# Pricing tables (USD per token)
OPENAI_PRICING = {
    "gpt-5-nano": {"input": 0.05 / 1_000_000, "output": 0.40 / 1_000_000},
    "gpt-4o": {"input": 2.50 / 1_000_000, "output": 10.00 / 1_000_000},
    "gpt-4": {"input": 30.00 / 1_000_000, "output": 60.00 / 1_000_000},
}

# Ollama pricing (self-hosted = $0)
OLLAMA_PRICING = {"default": {"input": 0.0, "output": 0.0}}


class CostTracker:
    """
    Track and calculate LLM API costs.

    Supports multiple providers (OpenAI, Ollama) and provides detailed
    breakdowns by operation type (planner, investigator, judge).

    Attributes:
        provider (str): LLM provider name ('openai' or 'ollama')
        model_name (str): Specific model being used
        llm_client: Reference to LLM client with token usage tracking

    Example:
        >>> tracker = CostTracker('openai', 'gpt-5-nano')
        >>> tracker.llm_client = my_llm_client
        >>> cost_data = tracker.calculate_cost()
        >>> tracker.print_summary()
    """

    def __init__(self, provider: str, model_name: str):
        """
        Initialize cost tracker.

        Args:
            provider: LLM provider ('openai' or 'ollama')
            model_name: Name of the model being used
        """
        self.provider = provider
        self.model_name = model_name
        self.llm_client = None  # Will be set later

    def get_pricing(self) -> Dict[str, float]:
        """
        Get pricing for current provider/model.

        Returns:
            Dictionary with 'input' and 'output' pricing per token
        """
        if self.provider == "openai":
            # Try exact match first
            if self.model_name in OPENAI_PRICING:
                return OPENAI_PRICING[self.model_name]

            # Try prefix match (e.g., gpt-5-nano-2024-01-01 -> gpt-5-nano)
            for key in OPENAI_PRICING:
                if self.model_name.startswith(key):
                    return OPENAI_PRICING[key]

            # Default to gpt-4o pricing (conservative estimate)
            return OPENAI_PRICING["gpt-4o"]

        else:  # ollama
            return OLLAMA_PRICING["default"]

    def calculate_cost(self) -> Dict:
        """
        Calculate total cost from token usage.

        NOTE: Cost is now tracked automatically in TokenUsage during API calls.
        This method just retrieves and formats the already-calculated costs.

        Returns:
            Dictionary containing:
                - total_cost_usd: Total cost in USD (from TokenUsage)
                - input_cost_usd: Cost of input tokens (calculated for display)
                - output_cost_usd: Cost of output tokens (calculated for display)
                - total_tokens: Total tokens used
                - breakdown: Per-operation cost breakdown (from TokenUsage)
                - pricing: Pricing rates used (for reference)
        """
        if not self.llm_client:
            return {
                "total_cost_usd": 0.0,
                "input_cost_usd": 0.0,
                "output_cost_usd": 0.0,
                "total_tokens": 0,
                "input_tokens": 0,
                "output_tokens": 0,
                "breakdown": {},
                "pricing": {},
            }

        # Get summary from TokenUsage (includes cost tracked during API calls)
        usage_summary = self.llm_client.token_usage.get_summary()
        pricing = self.get_pricing()

        total_input_tokens = usage_summary["total_input_tokens"]
        total_output_tokens = usage_summary["total_output_tokens"]
        total_cost = usage_summary.get("total_cost_usd", 0.0)  # Cost from API calls

        # Calculate input/output breakdown for display (estimate based on pricing)
        input_cost = total_input_tokens * pricing["input"]
        output_cost = total_output_tokens * pricing["output"]

        # Per-operation breakdown (use cost from TokenUsage)
        breakdown = {}
        for operation, data in usage_summary["by_operation"].items():
            breakdown[operation] = {
                "input_tokens": data["input"],
                "output_tokens": data["output"],
                "total_tokens": data["input"] + data["output"],
                "cost_usd": data.get("cost", 0.0),  # Cost tracked during API calls
                "calls": data["count"],
            }

        return {
            "total_cost_usd": total_cost,  # Use actual tracked cost
            "input_cost_usd": input_cost,  # Estimate for breakdown
            "output_cost_usd": output_cost,  # Estimate for breakdown
            "total_tokens": total_input_tokens + total_output_tokens,
            "input_tokens": total_input_tokens,
            "output_tokens": total_output_tokens,
            "breakdown": breakdown,
            "pricing": pricing,
        }

    def print_summary(self):
        """Print formatted cost summary to console."""
        cost_data = self.calculate_cost()

        print(f"\n{Colors.BOLD}💰 Cost Analysis:{Colors.END}")
        print(f"{Colors.DIM}{'─' * 80}{Colors.END}")

        if self.provider == "ollama":
            print(f"  Provider: Ollama (self-hosted)")
            print(f"  {Colors.GREEN}Cost: $0.00 (no API charges){Colors.END}")
            print(f"  Estimated tokens: {cost_data['total_tokens']:,}")
        else:
            print(f"  Provider: {self.provider}")
            print(f"  Model: {self.model_name}")
            print(f"  {Colors.BOLD}Total cost: ${cost_data['total_cost_usd']:.4f}{Colors.END}")
            print(
                f"    • Input:  {cost_data['input_tokens']:,} tokens (${cost_data['input_cost_usd']:.4f})"
            )
            print(
                f"    • Output: {cost_data['output_tokens']:,} tokens (${cost_data['output_cost_usd']:.4f})"
            )

            # Per-operation breakdown
            if cost_data["breakdown"]:
                print(f"\n  {Colors.DIM}Per-operation breakdown:{Colors.END}")
                sorted_ops = sorted(cost_data["breakdown"].items(), key=lambda x: -x[1]["cost_usd"])
                for op, data in sorted_ops[:10]:  # Top 10
                    print(
                        f"    {op:40s} ${data['cost_usd']:7.4f}  "
                        f"({data['total_tokens']:,} tokens, {data['calls']} calls)"
                    )

        print(f"{Colors.DIM}{'─' * 80}{Colors.END}\n")
