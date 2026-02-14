"""
MicroPAD - Microservices Architecture Pattern Detection.

A sophisticated AI-powered system for detecting architectural patterns
in microservice-based code repositories using multi-phase LLM reasoning,
graph analysis, and semantic code understanding.

Main Components:
    - core: Pattern detection orchestration
    - analysis: Pattern analysis and investigation
    - repository: Code parsing and graph construction
    - llm: Large language model integration
    - data: Statistical analysis and metrics
    - logging: Comprehensive logging infrastructure
    - utils: Utility functions and helpers
    - reporting: Report generation
    - config: Configuration management

Usage:
    from micropad.core import scanner
    scanner.main()
"""

__version__ = "2.0.0"
__author__ = "MicroPAD Team"
__license__ = "MIT"

# Core exports

__all__ = ["__version__"]