"""Core transformation utilities for the data pipeline skill."""

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any


def read_csv(filepath: str) -> list[dict[str, Any]]:
    """Read a CSV file and return a list of row dictionaries."""
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {filepath}")

    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


def write_json(data: list[dict[str, Any]], filepath: str) -> None:
    """Write data to a JSON file."""
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)


def transform_dates(records: list[dict[str, Any]], date_fields: list[str]) -> list[dict[str, Any]]:
    """Convert date fields to ISO 8601 format."""
    date_formats = ["%Y-%m-%d", "%m/%d/%Y", "%d-%m-%Y", "%Y/%m/%d"]
    result = []

    for record in records:
        row = dict(record)
        for field in date_fields:
            if field in row and row[field]:
                for fmt in date_formats:
                    try:
                        dt = datetime.strptime(row[field], fmt)
                        row[field] = dt.isoformat()
                        break
                    except ValueError:
                        continue
        result.append(row)

    return result


def validate_schema(records: list[dict[str, Any]], required_fields: list[str]) -> list[str]:
    """Validate that all records contain required fields. Returns list of errors."""
    errors = []
    for i, record in enumerate(records):
        for field in required_fields:
            if field not in record or not record[field]:
                errors.append(f"Row {i + 1}: missing required field '{field}'")
    return errors
