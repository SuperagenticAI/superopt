# SuperOpt Evaluation Results

**Generated:** 2025-12-25 17:09:16

## Executive Summary

- **Baseline**: 10/10 tasks (100.0% success)
- **Superopt**: 10/10 tasks (100.0% success)

## Table 1: Method Comparison

| Metric | Baseline | Superopt |
|--------|--------|--------|
| Success Rate | 100.0% | 100.0% |
| Avg Duration (s) | 20.07 | 107.41 |
| Avg Tool Calls | 1.8 | 2.3 |
| Avg Retries | 0.00 | 1.50 |
| Optimization Steps | N/A | 1.5 |
| Convergence Rate | N/A | 100% |

## Key Findings

1. **Both methods achieve 100% success rate** on this task set
2. SuperOpt requires **1.5 optimization steps** on average
3. **100% of tasks converge** to stable environment
4. SuperOpt takes 5.4x longer due to optimization overhead

## Per-Task Analysis

| Task | Baseline | Superopt |
|------|--------|--------|
| Create a Python function that calculates the facto... | PASS (6.8s) | PASS (88.2s) |
| Write a function to find the maximum value in a li... | PASS (8.0s) | PASS (87.3s) |
| Create a function that reverses a string. The func... | PASS (9.0s) | PASS (44.5s) |
| Write a function to calculate the average of a lis... | PASS (10.4s) | PASS (88.4s) |
| Create a function that sorts a list of dictionarie... | PASS (11.7s) | PASS (51.1s) |
| Write a function to merge two sorted lists. The fu... | PASS (14.1s) | PASS (55.4s) |
| Create a function that validates an email address.... | PASS (18.5s) | PASS (18.6s) |
| Write a function to count word frequency in a text... | PASS (27.2s) | PASS (137.2s) |
| Create a function that finds the longest common su... | PASS (21.7s) | PASS (218.4s) |
| Write a function to parse a date string in format ... | PASS (73.3s) | PASS (284.9s) |

## Resource Usage

| Method | Total Duration (s) | Tokens Sent | Tokens Received |
|--------|-------------------|-------------|-----------------|
| Baseline | 200.7 | 4,117,700 | 4,578 |
| Superopt | 1074.1 | 0 | 0 |

## Paper Recommendations

- Current task set is **too simple** - all methods achieve 100% success
- Consider using **harder tasks** that demonstrate optimization value
- Alternative: Focus on **efficiency metrics** (tokens, duration, retries)
