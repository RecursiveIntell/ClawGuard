---
name: code-metrics
description: Analyze code quality metrics and generate reports
version: 1.3.0
author: metrics-lab
metadata:
  openclaw:
    category: developer-tools
requires:
  bins:
    - python3
---

# Code Metrics

Analyze code quality metrics including complexity, maintainability, and test coverage.

## Features

- Cyclomatic complexity analysis
- Maintainability index calculation
- Lines of code statistics
- Test coverage integration

## Usage

### Analyze a File

```
Analyze the code metrics for src/main.py
```

### Generate Report

```
Generate a full metrics report for the project
```

## Implementation

The analysis engine is in `loader.py`, which handles loading analysis plugins
and running them against source files.
