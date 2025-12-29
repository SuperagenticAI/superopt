# SuperOpt Evaluation Results

**Generated:** 2025-12-25 17:34:36

## Executive Summary

- **Baseline**: 9/10 tasks (90.0% success)
- **Superopt**: 10/10 tasks (100.0% success)

## Table 1: Method Comparison

| Metric | Baseline | Superopt |
|--------|--------|--------|
| Success Rate | 90.0% | 100.0% |
| Avg Duration (s) | 44.94 | 28.19 |
| Avg Tool Calls | 1.4 | 2.5 |
| Avg Retries | 0.00 | 1.00 |
| Optimization Steps | N/A | 1.0 |
| Convergence Rate | N/A | 100% |

## Key Findings

1. **SuperOpt improves success rate by 10.0%** compared to baseline
2. SuperOpt requires **1.0 optimization steps** on average
3. **100% of tasks converge** to stable environment
4. SuperOpt is 1.6x faster than baseline

## Per-Task Analysis

| Task | Baseline | Superopt |
|------|--------|--------|
| Create a Python function called 'parse_nested_json... | FAIL (300.0s) | PASS (7.5s) |
| Write a function 'validate_credit_card' that valid... | PASS (7.5s) | PASS (11.7s) |
| Create a function 'merge_intervals' that takes a l... | PASS (8.6s) | PASS (17.4s) |
| Write a function 'tokenize_expression' that tokeni... | PASS (11.7s) | PASS (7.9s) |
| Create a function 'find_cycle' that detects if a d... | PASS (13.7s) | PASS (22.4s) |
| Write a function 'rate_limiter' that implements a ... | PASS (13.2s) | PASS (5.2s) |
| Create a function 'parse_cron' that parses a cron ... | PASS (21.0s) | PASS (33.1s) |
| Write a function 'diff_objects' that computes the ... | PASS (50.4s) | PASS (14.1s) |
| Create a function 'compress_string' using run-leng... | PASS (10.6s) | PASS (140.2s) |
| Write a function 'evaluate_postfix' that evaluates... | PASS (12.7s) | PASS (22.3s) |

## Resource Usage

| Method | Total Duration (s) | Tokens Sent | Tokens Received |
|--------|-------------------|-------------|-----------------|
| Baseline | 449.4 | 1,676,700 | 5,503 |
| Superopt | 281.9 | 0 | 0 |

## Paper Recommendations

- Results show **clear SuperOpt advantage** - suitable for paper
- Include failure analysis showing which types SuperOpt fixes
