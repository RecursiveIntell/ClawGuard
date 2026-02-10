# Test Fixtures

Each subdirectory is a self-contained OpenClaw skill package used for testing
ClawGuard's analysis pipeline.

## Clean Skills (should score well)

| Fixture | Description |
|---------|-------------|
| `clean_skill/` | Legitimate GitHub integration skill with proper frontmatter and metadata |
| `clean_complex_skill/` | Legitimate complex skill with multiple scripts, install instructions, and env requirements |

## Malicious / Risky Skills (should be flagged)

| Fixture | Primary Threat | Description |
|---------|---------------|-------------|
| `malicious_credential_harvester/` | Credential Exposure | Reads .env and exfiltrates via curl in bundled setup.sh |
| `prompt_injection_skill/` | Prompt Injection | Hidden instructions targeting HEARTBEAT.md |
| `obfuscated_payload/` | Obfuscation + Malware | base64 decode to exec pattern in helper.py |
| `typosquat_skill/` | Typosquatting | Named "githuh" (typosquat of "github") |
| `social_engineering_skill/` | Social Engineering | curl\|bash prerequisites (ClickFix-style attack) |
| `excessive_permissions_skill/` | Excessive Permissions | sudo and root env vars for a simple text formatter |
| `memory_manipulation_skill/` | Memory Manipulation | Modifies MEMORY.md and SOUL.md |
| `supply_chain_timebomb/` | Supply Chain | Remote URL import in bundled loader.py |
