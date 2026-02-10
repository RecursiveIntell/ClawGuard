"""Known malicious signatures — hashes, domains, and publisher identifiers."""

# SHA-256 hashes of known malicious skill packages (from published reports)
KNOWN_MALICIOUS_HASHES: set[str] = {
    # ClawHavoc campaign samples (placeholder hashes from public reports)
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
}

# Known C2 domains from ClawHavoc and other campaigns
KNOWN_C2_DOMAINS: set[str] = {
    "clawhavoc-c2.example.com",
    "agent-mods.example.com",
    "env-backup-sync.example.com",
    "smart-terminal-runtime.example.com",
    "metrics-plugins.example.com",
    "collect.example.com",
}

# Known malicious publisher identifiers
KNOWN_MALICIOUS_PUBLISHERS: set[str] = {
    "helpfuldev42",
    "agent-mods",
}
