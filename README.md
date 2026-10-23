# ClawGuard

<!-- last-verified: 2026-10-23 -->

Security analysis platform for AI agent skills (OpenClaw SKILL.md format).

ClawGuard scans skill packages for malware, prompt injection, credential harvesting, social engineering, obfuscation, and supply chain risks using static analysis, AST inspection, YARA pattern matching, and LLM-powered semantic review.

## Features

- **Multi-layer analysis** — Static regex patterns, YARA rules, tree-sitter AST inspection (Python + Bash), and optional LLM semantic review
- **Trust scoring** — Weighted 0-100 score with letter grades (A-F) and actionable recommendations (PASS / CAUTION / REVIEW / BLOCK)
- **11 threat categories** — Malware, prompt injection, credential exposure, social engineering, network exfiltration, obfuscation, excessive permissions, typosquatting, supply chain, memory manipulation, best practices
- **Multiple interfaces** — CLI, REST API, and web frontend
- **Report export** — JSON, Markdown, and self-contained HTML reports
- **ClawHub integration** — Scan skills directly from the ClawHub registry by URL, or bulk-scan top skills

## Scope and current limits

Scores are heuristic triage results, not a security certification or permission to execute a skill. False negatives and false positives are possible. In the current LLM analyzer, API errors and malformed responses can produce no LLM findings; inspect analyzer coverage and logs rather than treating a high score as proof of safety.

The CLI can optionally send skill text, metadata and bundled scripts to Anthropic. Use `--no-llm` for a local-only skill scan; URL and registry scans still require network access. The current REST scan routes explicitly disable LLM analysis.

The REST service stores scan history in process memory. PostgreSQL repository/schema code exists, but merely setting a database URL does not enable persistent history in `clawguard/api/app.py`. Keep this development API on loopback: it accepts server-side local paths and ZIP uploads, and does not implement an authentication boundary.

## Quick Start

```bash
git clone https://github.com/RecursiveIntell/ClawGuard.git
cd ClawGuard
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
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

# Bulk-scan top ClawHub skills (network access required; default limit is 100)
clawguard bulk-scan --limit 50
```

`clawguard --help` and `clawguard <command> --help` show the full command help; `clawguard --version` prints the installed version. The CLI options relevant to these workflows are:

| Command | Option | Behavior and default |
|---|---|---|
| `scan` | `--url URL` | Fetch a skill from ClawHub; requires network access. |
| `scan` | `--json` | Print JSON instead of formatted text. |
| `scan`, `scan-all`, `watch` | `--no-llm` | Skip LLM analysis. |
| `scan` | `-o, --output PATH` | Write the report to a file; default is standard output. |
| `scan` | `-v, --verbose` | Include finding evidence in the text report when available. |
| `scan`, `scan-all` | `-q, --quiet` | Print only the score and recommendation (and skill name for `scan-all`). |
| `scan-all` | `--json` | Print results as a JSON array. |
| `bulk-scan` | `--limit N` | Number of registry skills to scan; default: `100`. |
| `bulk-scan` | `--json` | Print results as JSON. |

For `scan` and `scan-all`, exit codes are: `0` PASS, `1` CAUTION, `2` REVIEW, `3` BLOCK. `watch` and `bulk-scan` do not use these recommendation-based exit codes.

### API

```bash
# The upload route also requires python-multipart (not currently declared in pyproject.toml)
python -m pip install python-multipart
uvicorn clawguard.api.app:app --host 127.0.0.1 --port 8000 --reload
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

The frontend rewrites `/api/*` to `http://localhost:8000`; run the API alongside it. Dark-themed Next.js 15 app with:
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
  db/             # PostgreSQL schema/repository; not wired into current API history
frontend/         # Next.js 15 + Tailwind CSS 4 web interface
tests/            # Automated tests and fixture skills; use pytest for current results
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

## Configuration

Environment variables and a local `.env` file are read by [clawguard/config.py](clawguard/config.py). Keep secrets out of version control; `.env` files are ignored by `.gitignore`. For CLI LLM analysis, create an API key in the [Claude Console](https://platform.claude.com/settings/keys) (Anthropic API keys commonly begin `sk-ant-…`). Supply it through a local secret manager where available, or use either shell form below with a placeholder—not a real key:

```bash
export CLAWGUARD_ANTHROPIC_API_KEY="YOUR_ANTHROPIC_API_KEY"
# Or set it for one command:
CLAWGUARD_ANTHROPIC_API_KEY="YOUR_ANTHROPIC_API_KEY" clawguard scan path/to/skill/
```

The CLI sends skill text, metadata, and bundled scripts to Anthropic when LLM analysis is enabled; API usage may incur provider charges. Avoid putting real keys in shell history; never commit them.

| Environment variable | Default | Current effect |
|---|---|---|
| `CLAWGUARD_ANTHROPIC_API_KEY` | unset | Enables the CLI's optional Anthropic analysis. |
| `CLAWGUARD_CLAWGUARD_MODEL` | `claude-sonnet-4-5-20250929` | Selects the model; the field name already includes `CLAWGUARD_`, so the configured prefix appears twice. |
| `CLAWGUARD_MAX_SKILL_SIZE_MB` | `10` | Maximum size per bundled file read for analysis; larger files are skipped. |
| `CLAWGUARD_DATABASE_URL` | `postgresql://localhost:5432/clawguard` | Used by the separate database repository; setting it does not enable persistent API history. |
| `CLAWGUARD_REDIS_URL` | `redis://localhost:6379/0` | Declared configuration only; no active worker/queue integration currently consumes it. |
| `CLAWGUARD_LOG_LEVEL` | `INFO` | Declared setting, but the current CLI logging configuration does not apply it. |

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
- PostgreSQL/Redis are relevant to the separate infrastructure modules; the current API history is in-memory
- Anthropic API key (optional, for CLI LLM analysis; see configuration above)
