# ClawGuard

Security analysis platform for AI agent skills (OpenClaw SKILL.md format).

ClawGuard scans skill packages for malware, prompt injection, credential harvesting, social engineering, obfuscation, and supply chain risks using static analysis, AST inspection, YARA pattern matching, and LLM-powered semantic review.

## Features

- **Multi-layer analysis** — Static regex patterns, YARA rules, tree-sitter AST inspection (Python + Bash), and optional LLM semantic review
- **Trust scoring** — Weighted 0-100 score with letter grades (A-F) and actionable recommendations (PASS / CAUTION / REVIEW / BLOCK)
- **11 threat categories** — Malware, prompt injection, credential exposure, social engineering, network exfiltration, obfuscation, excessive permissions, typosquatting, supply chain, memory manipulation, best practices
- **Multiple interfaces** — CLI, REST API, and web frontend
- **Report export** — JSON, Markdown, and self-contained HTML reports
- **ClawHub integration** — Scan skills directly from the ClawHub registry by URL, or bulk-scan top skills

## Quick Start

```bash
pip install -e ".[dev]"
```

### CLI

```bash
# Scan a local skill directory
clawguard scan path/to/skill/

# Scan from a ClawHub URL
clawguard scan --url https://clawhub.com/skills/author/name

# JSON output
clawguard scan path/to/skill/ --json

# Quiet mode (just score + recommendation)
clawguard scan path/to/skill/ --quiet

# Skip LLM analysis (faster, no API key needed)
clawguard scan path/to/skill/ --no-llm

# Scan all skills in a directory
clawguard scan-all ./skills/ --no-llm

# Write report to file
clawguard scan path/to/skill/ --output report.md

# Watch mode — re-scan on file changes
clawguard watch path/to/skill/

# Bulk-scan top ClawHub skills
clawguard bulk-scan --limit 50
```

Exit codes: `0` PASS, `1` CAUTION, `2` REVIEW, `3` BLOCK.

### API

```bash
uvicorn clawguard.api.app:app --reload
```

| Endpoint | Method | Description |
|---|---|---|
| `/api/health` | GET | Health check |
| `/api/scan` | POST | Submit scan (URL or local path) |
| `/api/scan/upload` | POST | Upload skill ZIP for scanning |
| `/api/scan/{id}` | GET | Get scan results |
| `/api/scans` | GET | List scan history (paginated) |

### Frontend

```bash
cd frontend
pnpm install
pnpm dev
```

Dark-themed Next.js 15 app with:
- Scan page with URL input, local path, and drag-and-drop ZIP upload
- Results page with animated trust score circle, expandable finding cards grouped by severity, and JSON/Markdown export
- History page with sortable columns and pagination

## Architecture

```
clawguard/
  parser/         # SKILL.md frontmatter, markdown, and script inventory
  analyzers/      # Static, AST (tree-sitter), and LLM analyzers
  rules/          # YARA rules and regex pattern library
  scoring/        # Weighted trust score engine
  pipeline.py     # Orchestrates parse → analyze → score → report
  reports/        # JSON, Markdown, and HTML report generators
  clawhub/        # ClawHub registry client and bulk scanning
  cli/            # Click CLI with Rich formatting
  api/            # FastAPI REST API
  db/             # PostgreSQL schema and asyncpg repository
frontend/         # Next.js 15 + Tailwind CSS 4 web interface
tests/            # 185 tests with 10 fixture skills
```

## Trust Score

Starts at 100 and deducts points per finding:

| Severity | Base Deduction |
|---|---|
| Critical | 40 |
| High | 20 |
| Medium | 10 |
| Low | 3 |
| Info | 0 |

Category multipliers boost deductions for higher-risk categories (malware 2x, prompt injection/credential exposure 1.5x). Diminishing returns apply per category (1st finding full, 2nd 0.5x, 3rd+ 0.25x).

## Development

```bash
pip install -e ".[dev]"

# Run tests
pytest

# Lint
ruff check clawguard/ tests/

# Type check the frontend
cd frontend && pnpm build
```

## Requirements

- Python 3.12+
- Node.js 20+ and pnpm (for frontend)
- PostgreSQL (optional, for persistent scan history)
- Anthropic API key (optional, for LLM analysis)
