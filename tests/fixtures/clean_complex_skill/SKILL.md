---
name: data-pipeline
description: Build and manage data transformation pipelines with validation
version: 3.1.0
author: dataworks-team
license: Apache-2.0
metadata:
  openclaw:
    category: data-engineering
    verified: true
    downloads: 8350
requires:
  bins:
    - python3
    - pip
  env:
    - DATA_PIPELINE_INPUT_DIR
    - DATA_PIPELINE_OUTPUT_DIR
  config:
    max_workers: 4
    log_level: INFO
    validate_schema: true
install:
  - description: Install Python dependencies
    command: bash install.sh
---

# Data Pipeline

Build and manage data transformation pipelines with built-in validation and error handling.

## Features

- **Pipeline Builder**: Define multi-step data transformation pipelines
- **Schema Validation**: Validate data at each pipeline stage
- **Error Handling**: Configurable error strategies (skip, retry, fail)
- **Parallel Processing**: Process large datasets with configurable worker count
- **Audit Logging**: Track all transformations for compliance

## Installation

Run the included install script:

```bash
bash install.sh
```

This installs the required Python packages (pandas, jsonschema) into the skill's
virtual environment.

## Usage

### Create a Pipeline

```
Create a data pipeline that reads CSV from $DATA_PIPELINE_INPUT_DIR,
validates against the user schema, transforms dates to ISO format,
and writes JSON to $DATA_PIPELINE_OUTPUT_DIR
```

### Run with Validation

```
Run the pipeline with schema validation enabled on the sales_data.csv file
```

## Architecture

The pipeline uses a directed acyclic graph (DAG) model where each node
is a transformation step. The `utils.py` module provides the core
transformation functions.

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `max_workers` | 4 | Parallel processing threads |
| `log_level` | INFO | Logging verbosity |
| `validate_schema` | true | Enable schema validation |
