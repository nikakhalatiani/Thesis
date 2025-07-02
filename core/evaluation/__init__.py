"""
Core evaluation module for property testing and result formatting.

This module contains utilities for:
- Evaluating library against functions under test
- Formatting test results and statistics
- Managing test outcomes and performance metrics
"""

from .property_evaluator import PropertyEvaluator

__all__ = [
    'PropertyEvaluator',
]