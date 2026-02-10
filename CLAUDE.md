# ClawGuard — Agent Instructions

## What This Is
ClawGuard is a security analysis platform for AI agent skills (OpenClaw SKILL.md format).
It scans skills for malware, prompt injection, credential harvesting, and supply chain risks.

## Stack
- Python 3.12+, FastAPI, Click, Anthropic SDK
- tree-sitter (AST), yara-python (pattern matching)
- PostgreSQL, Redis + Celery (async jobs)
- Next.js 15, React 19, TypeScript, Tailwind CSS 4

## Conventions
- Type hints on ALL function signatures. Use `dataclasses` or Pydantic `BaseModel`.
- `ruff` for linting + formatting. Config in pyproject.toml.
- `pytest` for testing. Every module gets a corresponding test file.
- Errors: Use custom exception hierarchy rooted at `ClawGuardError`.
  Never swallow exceptions. Always include actionable context.
- Logging: `structlog` (structured JSON logging). No print().
- Async: FastAPI routes are async. Analyzers are sync (CPU-bound).
  Celery workers handle long-running scans.
- All analyzer outputs conform to the `Finding` dataclass (see analyzers/base.py).
- All public functions have docstrings.

## Non-Negotiable Rules
1. NEVER execute code from a skill being scanned. Analysis is read-only.
2. NEVER store API keys in code. Use environment variables via config.py.
3. ALL external input (skill content) is untrusted. Sanitize before any processing.
4. Tests use fixtures from tests/fixtures/, never fetch from live ClawHub.
5. Every analyzer must implement AnalyzerBase ABC.
6. The pipeline is linear: parse -> static -> AST -> LLM -> score -> report.
   No analyzer depends on another analyzer's output.

## File Boundaries
- Don't touch files outside your ticket's scope.
- Shared types go in analyzers/base.py or a new shared module.
- If you need a type from another module, import it; don't redefine it.

## Role Routing Hints
- Parser, API, CLI, reports, database, frontend → @coder
- YARA rules, test fixtures, threat patterns → @security
- Pipeline orchestration, shared types → @architect
- All test files → @tester
- Post-batch integration checks → @reviewer
