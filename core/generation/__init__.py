"""
Core generation module for handling input generation and user module loading.

This module contains utilities for:
- Generating test inputs using grammar configurations
- Loading and processing user-defined modules
- Handling grammar and parser overrides
"""

from .input_generator import InputGenerator
from .user_module_loader import (
    load_user_module,
    extract_overrides,
    process_grammar_override,
    process_parser_override,
    extract_functions_from_classes
)

__all__ = [
    'InputGenerator',
    'load_user_module',
    'extract_overrides',
    'process_grammar_override',
    'process_parser_override',
    'extract_functions_from_classes'
]