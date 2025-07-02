"""
Core module for the property inference system.

This module provides the main orchestration capabilities and exports
key components from all sub-modules for convenient access.

Architecture Overview:
- core/generation/: Input generation using grammar-based fuzzing
- core/evaluation/: Property testing and result evaluation
- core/correlation/: Constraint inference and pattern correlation
- core/util/: Configuration management
- core/registry/: Property registry and organization
"""

# Main orchestrator
from .property_inference_engine import PropertyInferenceEngine

# Configuration management
from .config import PropertyInferenceConfig

# Registry management
from core.library.registry import PropertyRegistry

# Function testing utilities
from util.function_under_test import (
    FunctionUnderTest,
    CombinedFunctionUnderTest,
    ComparisonStrategy,
    FunctionConvertError
)

# Sub-module exports for convenience
from .generation import (
    InputGenerator,
    load_user_module,
    extract_overrides,
    process_grammar_override,
    process_parser_override,
    extract_functions_from_classes
)

from .evaluation import (
    PropertyEvaluator,
)

from .correlation import (
    ConstraintInferenceEngine,
    LocalModel,
    OllamaService,
)

# Properties module (keeping existing exports)
from . import library

__all__ = [
    # Main orchestrator
    'PropertyInferenceEngine',

    # Configuration and registry
    'PropertyInferenceConfig',
    'PropertyRegistry',

    # Function testing
    'FunctionUnderTest',
    'CombinedFunctionUnderTest',
    'ComparisonStrategy',
    'FunctionConvertError',

    # Generation utilities
    'InputGenerator',
    'load_user_module',
    'extract_overrides',
    'process_grammar_override',
    'process_parser_override',
    'extract_functions_from_classes',

    # Evaluation utilities
    'PropertyEvaluator',

    # Correlation utilities
    'ConstraintInferenceEngine',
    'LocalModel',
    'OllamaService',

    # Properties module
    'properties'
]