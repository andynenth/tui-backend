#!/usr/bin/env python3
"""
AI Declaration Tests - Modular Test Suite

This package provides comprehensive testing of AI declaration strategy across
all major strategic scenarios, organized by category for better coverage
and maintainability.

Test Categories:
- baseline: Original 18 regression test scenarios
- position_strategy: Starter vs non-starter behaviors (12 tests)
- field_strength: Weak/strong/mixed field adaptations (15 tests)  
- combo_opportunity: Viable combo detection and filtering (18 tests)
- pile_room_constraints: Zero room, limited room, room mismatches (12 tests)
- opener_reliability: Strong/marginal/no opener scenarios (15 tests)
- general_red_special: Game-changing GENERAL_RED scenarios (9 tests)
- edge_cases: Complex rule interactions and constraints (12 tests)

Total Tests: 111 comprehensive scenarios vs original 18 examples

Usage:
    # Run all tests
    pytest tests/ai_declaration/
    
    # Run specific category
    pytest tests/ai_declaration/test_baseline.py
    pytest tests/ai_declaration/test_combo_opportunity.py
    
    # Run with verbose output
    pytest tests/ai_declaration/ -v
    
    # Run individual test modules directly
    python tests/ai_declaration/test_baseline.py
"""

__version__ = "1.0.0"
__author__ = "AI Strategic Analysis Team"

# Import key components for external usage
from .conftest import (
    TestScenario,
    TestCategory,
    DifficultyLevel,
    TestResult,
    execute_test_scenario,
    run_category_tests,
    parse_hand,
    create_piece
)

__all__ = [
    'TestScenario',
    'TestCategory', 
    'DifficultyLevel',
    'TestResult',
    'execute_test_scenario',
    'run_category_tests',
    'parse_hand',
    'create_piece'
]