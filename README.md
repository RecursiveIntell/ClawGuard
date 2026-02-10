# ClawGuard

Security analysis platform for AI agent skills (OpenClaw SKILL.md format).

ClawGuard scans skill packages for malware, prompt injection, credential harvesting,
social engineering, and supply chain risks using static analysis, AST inspection,
and LLM-powered semantic review.

## Quick Start

```bash
pip install -e ".[dev]"
clawguard scan path/to/skill/
```

## Development

```bash
pip install -e ".[dev]"
ruff check clawguard/
pytest
```
