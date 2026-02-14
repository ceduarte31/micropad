"""
Configuration management module.

Centralized configuration with validation and environment variable support.
"""

from micropad.config.settings import *

__all__ = ["get_config_summary", "validate_configuration"]
