"""Compiled regex patterns for the static analyzer, grouped by category."""

import re

# ── Credential Exposure ────────────────────────────────────────────────────────

AWS_ACCESS_KEY = re.compile(r"AKIA[0-9A-Z]{16}")
GITHUB_TOKEN = re.compile(r"(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9_]{36,}")
GENERIC_API_KEY = re.compile(
    r"""(?:api[_-]?key|secret[_-]?key|access[_-]?token)\s*[=:]\s*["'][a-zA-Z0-9]{16,}["']""",
    re.IGNORECASE,
)
SK_LIVE_KEY = re.compile(r"sk-[a-zA-Z0-9]{20,}")
BEARER_TOKEN = re.compile(r"Bearer\s+[a-zA-Z0-9_\-\.]{20,}")
PRIVATE_KEY_HEADER = re.compile(r"-----BEGIN\s+\w*\s*PRIVATE\s+KEY-----")
ENV_FILE_READ = re.compile(r"""(?:cat|open\s*\()\s*.*\.env""")
BROAD_ENV_ACCESS = re.compile(r"(?:os\.environ(?!\[)|process\.env(?!\[)|printenv|env\s*>)")

CREDENTIAL_PATTERNS = [
    ("AWS access key", AWS_ACCESS_KEY),
    ("GitHub token", GITHUB_TOKEN),
    ("Generic API key", GENERIC_API_KEY),
    ("Stripe/OpenAI secret key", SK_LIVE_KEY),
    ("Bearer token", BEARER_TOKEN),
    ("Private key", PRIVATE_KEY_HEADER),
    (".env file access", ENV_FILE_READ),
    ("Broad environment access", BROAD_ENV_ACCESS),
]

# ── Network Exfiltration ──────────────────────────────────────────────────────

CURL_POST = re.compile(r"curl\s+.*-X\s*POST|curl\s+.*--data|curl\s+.*-d\s")
WGET_DOWNLOAD = re.compile(r"wget\s+")
REQUESTS_POST = re.compile(r"requests\.(?:post|put)\s*\(")
FETCH_CALL = re.compile(r"fetch\s*\(")
URLLIB_OPEN = re.compile(r"urllib\.request\.urlopen")
SOCKET_CONNECT = re.compile(r"socket\..*connect\s*\(")

NETWORK_PATTERNS = [
    ("curl POST request", CURL_POST),
    ("wget download", WGET_DOWNLOAD),
    ("Python requests POST", REQUESTS_POST),
    ("JavaScript fetch call", FETCH_CALL),
    ("urllib request", URLLIB_OPEN),
    ("Socket connection", SOCKET_CONNECT),
]

# ── Shell Execution ───────────────────────────────────────────────────────────

EVAL_EXEC = re.compile(r"\b(?:eval|exec)\s*\(")
SUBPROCESS_CALL = re.compile(r"subprocess\.(?:call|run|Popen|check_output)\s*\(")
OS_SYSTEM = re.compile(r"os\.(?:system|popen)\s*\(")
COMPILE_EXEC = re.compile(r"compile\s*\(.*exec")
DUNDER_IMPORT = re.compile(r"__import__\s*\(")

SHELL_EXEC_PATTERNS = [
    ("eval/exec call", EVAL_EXEC),
    ("subprocess call", SUBPROCESS_CALL),
    ("os.system/popen", OS_SYSTEM),
    ("compile+exec", COMPILE_EXEC),
    ("__import__", DUNDER_IMPORT),
]

# ── Obfuscation ──────────────────────────────────────────────────────────────

BASE64_DECODE = re.compile(r"base64\.b64decode|atob\(|bytes\.fromhex")
LONG_BASE64_STRING = re.compile(r"[A-Za-z0-9+/]{100,}={0,2}")
STRING_CONCAT_HTTP = re.compile(r"""["']h["']\s*\+\s*["']t["']\s*\+\s*["']t["']\s*\+\s*["']p""")

OBFUSCATION_PATTERNS = [
    ("Base64/hex decoding", BASE64_DECODE),
    ("Long encoded string", LONG_BASE64_STRING),
    ("String concatenation obfuscation", STRING_CONCAT_HTTP),
]

# ── Social Engineering ────────────────────────────────────────────────────────

CURL_PIPE_BASH = re.compile(r"curl\s+[^\n]*\|\s*(?:sudo\s+)?(?:ba)?sh")
WGET_PIPE_BASH = re.compile(r"wget\s+[^\n]*\|\s*(?:sudo\s+)?(?:ba)?sh")
CHMOD_PLUS_X = re.compile(r"chmod\s+\+x\s+")

SOCIAL_ENGINEERING_PATTERNS = [
    ("curl piped to shell", CURL_PIPE_BASH),
    ("wget piped to shell", WGET_PIPE_BASH),
    ("chmod +x on file", CHMOD_PLUS_X),
]

# ── Memory Manipulation ──────────────────────────────────────────────────────

MEMORY_FILE_WRITE = re.compile(
    r"(?:HEARTBEAT|MEMORY|SOUL)\.md",
)
CLAWDBOT_JSON = re.compile(r"clawdbot\.json")

MEMORY_PATTERNS = [
    ("Agent memory file reference", MEMORY_FILE_WRITE),
    ("clawdbot.json reference", CLAWDBOT_JSON),
]

# ── Suspicious URLs ──────────────────────────────────────────────────────────

PASTE_SERVICE = re.compile(r"(?:pastebin\.com|hastebin\.com|glot\.io|dpaste\.org|paste\.ee)")
URL_SHORTENER = re.compile(r"(?:bit\.ly|tinyurl\.com|t\.co/|is\.gd/)")
DISCORD_WEBHOOK = re.compile(r"discord(?:app)?\.com/api/webhooks")
TELEGRAM_BOT = re.compile(r"api\.telegram\.org/bot")
RAW_GIST = re.compile(r"gist\.githubusercontent\.com")

SUSPICIOUS_URL_PATTERNS = [
    ("Paste service URL", PASTE_SERVICE),
    ("URL shortener", URL_SHORTENER),
    ("Discord webhook", DISCORD_WEBHOOK),
    ("Telegram bot API", TELEGRAM_BOT),
    ("Raw GitHub gist", RAW_GIST),
]

# ── Excessive Permissions ────────────────────────────────────────────────────

POWERFUL_BINS = {"sudo", "nmap", "tcpdump", "strace", "ltrace", "gdb", "ncat", "nc", "netcat"}
