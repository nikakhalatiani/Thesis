"""
Core correlation module for constraint inference and pattern discovery.

This module contains utilities for:
- Inferring constraints from execution traces
- Correlating patterns between passing and failing test cases
- Model services for constraint generation
- Prompt building and constraint parsing
"""

from .constraint_model import ConstraintModel
from .model_services import ModelService, OllamaService, ServiceHealthChecker, OllamaHealthChecker
from .prompt_builder import PromptBuilder
from .constraint_parser import ConstraintParser
from .local_model import LocalModel
from .constraint_inference_engine import ConstraintInferenceEngine

__all__ = [
    'ConstraintModel',
    'ModelService',
    'OllamaService',
    'ServiceHealthChecker',
    'OllamaHealthChecker',
    'PromptBuilder',
    'ConstraintParser',
    'LocalModel',
    'ConstraintInferenceEngine'
]