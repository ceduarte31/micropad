"""
LLM integration module.

Provides abstraction layer for multiple LLM providers (OpenAI, Ollama)
and handles prompt generation for the three-phase detection pipeline.
"""

from micropad.llm.agent import AIAgent
from micropad.llm.client import LLMClient
from micropad.llm.prompts import PromptBuilder

__all__ = ["LLMClient", "AIAgent", "PromptBuilder"]
