"""
Cost Tracking Module for LLM API Usage.

This module tracks token usage and calculates costs for different LLM providers
(OpenAI, Ollama, etc.) used throughout the pattern detection pipeline.

Classes:
    CostTracker: Tracks and calculates LLM API costs based on token usage.
"""

from typing import Dict, Optional

from micropad.logging.ui import Colors

# Ollama Cloud is a flat subscription, not billed per token.
OLLAMA_PRICING = {"default": {"input": 0.0, "output": 0.0}}


class CostTracker:
    """
    Track LLM token usage (Ollama Cloud has no per-token cost to calculate).

    Provides detailed token-usage breakdowns by operation type
    (planner, investigator, judge).

    Attributes:
        provider (str): LLM provider name (always 'ollama')
        model_name (str): Specific model being used
        llm_client: Reference to LLM client with token usage tracking

    Example:
        >>> tracker = CostTracker('ollama', 'gpt-oss:120b')
        >>> tracker.llm_client = my_llm_client
        >>> cost_data = tracker.calculate_cost()
        >>> tracker.print_summary()
    """

    def __init__(self, provider: str, model_name: str):
        """
        Initialize cost tracker.

        Args:
            provider: LLM provider (always 'ollama')
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
        return OLLAMA_PRICING["default"]

    def calculate_cost(self) -> Dict:
        """
        Summarize token usage. Ollama Cloud has no per-token cost.

        Returns:
            Dictionary containing total/per-operation token counts.
        """
        if not self.llm_client:
            return {"total_tokens": 0, "input_tokens": 0, "output_tokens": 0, "breakdown": {}}

        usage_summary = self.llm_client.token_usage.get_summary()

        breakdown = {}
        for operation, data in usage_summary["by_operation"].items():
            breakdown[operation] = {
                "input_tokens": data["input"],
                "output_tokens": data["output"],
                "total_tokens": data["input"] + data["output"],
                "calls": data["count"],
            }

        return {
            "total_tokens": usage_summary["total_input_tokens"] + usage_summary["total_output_tokens"],
            "input_tokens": usage_summary["total_input_tokens"],
            "output_tokens": usage_summary["total_output_tokens"],
            "breakdown": breakdown,
        }

    def print_summary(self):
        """Print formatted token usage summary to console."""
        cost_data = self.calculate_cost()

        print(f"\n{Colors.BOLD}Token Usage:{Colors.END}")
        print(f"{Colors.DIM}{'─' * 80}{Colors.END}")
        print(f"  Provider: Ollama Cloud")
        print(f"  Model: {self.model_name}")
        print(f"  Total tokens: {cost_data['total_tokens']:,}")

        if cost_data["breakdown"]:
            print(f"\n  {Colors.DIM}Per-operation breakdown:{Colors.END}")
            sorted_ops = sorted(cost_data["breakdown"].items(), key=lambda x: -x[1]["total_tokens"])
            for op, data in sorted_ops[:10]:  # Top 10
                print(f"    {op:40s} {data['total_tokens']:,} tokens ({data['calls']} calls)")

        print(f"{Colors.DIM}{'─' * 80}{Colors.END}\n")
