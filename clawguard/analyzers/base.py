"""Shared types for all ClawGuard analyzers."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum


class Severity(Enum):
    CRITICAL = "critical"  # Active malware, data exfil, RCE
    HIGH = "high"  # Credential exposure, prompt injection
    MEDIUM = "medium"  # Excessive permissions, suspicious patterns
    LOW = "low"  # Best practice violations, missing metadata
    INFO = "info"  # Informational observations


class Category(Enum):
    MALWARE = "malware"
    PROMPT_INJECTION = "prompt_injection"
    CREDENTIAL_EXPOSURE = "credential_exposure"
    SOCIAL_ENGINEERING = "social_engineering"
    NETWORK_EXFILTRATION = "network_exfiltration"
    OBFUSCATION = "obfuscation"
    EXCESSIVE_PERMISSIONS = "excessive_permissions"
    TYPOSQUATTING = "typosquatting"
    SUPPLY_CHAIN = "supply_chain"
    MEMORY_MANIPULATION = "memory_manipulation"  # HEARTBEAT.md, MEMORY.md, SOUL.md
    BEST_PRACTICE = "best_practice"


@dataclass
class Finding:
    """Single security finding from any analyzer."""

    analyzer: str  # e.g. "static", "ast", "llm"
    category: Category
    severity: Severity
    title: str  # Short description: "Hardcoded API key in setup.sh"
    detail: str  # Full explanation with evidence
    file: str | None = None  # File where found, if applicable
    line: int | None = None  # Line number, if applicable
    evidence: str | None = None  # The actual offending content (redacted if sensitive)
    cwe: str | None = None  # CWE ID if applicable
    recommendation: str = ""  # What to do about it


@dataclass
class SkillPackage:
    """Parsed representation of an OpenClaw skill."""

    name: str
    description: str
    path: str  # Local path to skill directory
    skill_md_raw: str  # Raw SKILL.md content
    frontmatter: dict  # Parsed YAML frontmatter
    instructions: str  # Markdown body (post-frontmatter)
    scripts: list[dict] = field(default_factory=list)  # {path, content, language}
    metadata: dict = field(default_factory=dict)  # metadata.openclaw block
    requires: dict = field(default_factory=dict)  # bins, env, config requirements
    install_instructions: list[dict] = field(default_factory=list)


class AnalyzerBase(ABC):
    """All analyzers implement this interface."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Analyzer identifier (e.g. 'static', 'ast', 'llm')."""

    @abstractmethod
    def analyze(self, skill: SkillPackage) -> list[Finding]:
        """Run analysis on a parsed skill. Returns list of findings."""

    def supports(self, skill: SkillPackage) -> bool:
        """Override to skip analysis for certain skills. Default: always run."""
        return True
