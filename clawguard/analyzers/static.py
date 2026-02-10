"""Static analyzer — regex and YARA-based pattern matching."""

from pathlib import Path

import structlog
import yara

from clawguard.analyzers.base import (
    AnalyzerBase,
    Category,
    Finding,
    Severity,
    SkillPackage,
)
from clawguard.rules import patterns
from clawguard.rules.signatures import KNOWN_C2_DOMAINS, KNOWN_MALICIOUS_PUBLISHERS

logger = structlog.get_logger()

YARA_RULES_DIR = Path(__file__).parent.parent / "rules" / "yara"

# Map YARA rule metadata category to Category enum
_CATEGORY_MAP: dict[str, Category] = {
    "credential_exposure": Category.CREDENTIAL_EXPOSURE,
    "prompt_injection": Category.PROMPT_INJECTION,
    "obfuscation": Category.OBFUSCATION,
    "network_exfiltration": Category.NETWORK_EXFILTRATION,
    "social_engineering": Category.SOCIAL_ENGINEERING,
}

# Map YARA rule metadata severity to Severity enum
_SEVERITY_MAP: dict[str, Severity] = {
    "critical": Severity.CRITICAL,
    "high": Severity.HIGH,
    "medium": Severity.MEDIUM,
    "low": Severity.LOW,
    "info": Severity.INFO,
}


def _load_yara_rules() -> yara.Rules | None:
    """Compile all YARA rules from the rules directory."""
    if not YARA_RULES_DIR.is_dir():
        logger.warning("yara_rules_dir_missing", path=str(YARA_RULES_DIR))
        return None

    filepaths = {}
    for yar_file in sorted(YARA_RULES_DIR.glob("*.yar")):
        filepaths[yar_file.stem] = str(yar_file)

    if not filepaths:
        return None

    try:
        return yara.compile(filepaths=filepaths)
    except yara.Error as e:
        logger.error("yara_compile_error", error=str(e))
        return None


class StaticAnalyzer(AnalyzerBase):
    """Pattern-matching analyzer using regex and YARA rules."""

    def __init__(self) -> None:
        self._yara_rules = _load_yara_rules()

    @property
    def name(self) -> str:
        return "static"

    def analyze(self, skill: SkillPackage) -> list[Finding]:
        """Run static pattern analysis on all skill content."""
        findings: list[Finding] = []

        # Build content map: filename -> content
        content_map = {"SKILL.md": skill.skill_md_raw}
        for script in skill.scripts:
            content_map[script["path"]] = script["content"]

        # Run regex patterns on each file
        for filename, content in content_map.items():
            findings.extend(self._check_regex_patterns(filename, content))

        # Run YARA rules on combined content
        findings.extend(self._check_yara(content_map))

        # Check for known malicious publishers
        findings.extend(self._check_signatures(skill))

        # Check for excessive permissions
        findings.extend(self._check_permissions(skill))

        # Check for known C2 domains in all content
        findings.extend(self._check_c2_domains(content_map))

        return findings

    def _check_regex_patterns(self, filename: str, content: str) -> list[Finding]:
        """Run all regex pattern groups against file content."""
        findings: list[Finding] = []
        lines = content.splitlines()

        pattern_groups: list[tuple[str, list, Category, Severity]] = [
            (
                "credential",
                patterns.CREDENTIAL_PATTERNS,
                Category.CREDENTIAL_EXPOSURE,
                Severity.HIGH,
            ),
            ("network", patterns.NETWORK_PATTERNS, Category.NETWORK_EXFILTRATION, Severity.MEDIUM),
            ("shell_exec", patterns.SHELL_EXEC_PATTERNS, Category.SUPPLY_CHAIN, Severity.MEDIUM),
            ("obfuscation", patterns.OBFUSCATION_PATTERNS, Category.OBFUSCATION, Severity.MEDIUM),
            (
                "social_eng",
                patterns.SOCIAL_ENGINEERING_PATTERNS,
                Category.SOCIAL_ENGINEERING,
                Severity.CRITICAL,
            ),
            ("memory", patterns.MEMORY_PATTERNS, Category.MEMORY_MANIPULATION, Severity.CRITICAL),
            (
                "suspicious_url",
                patterns.SUSPICIOUS_URL_PATTERNS,
                Category.NETWORK_EXFILTRATION,
                Severity.MEDIUM,
            ),
        ]

        for _group_name, pattern_list, category, default_severity in pattern_groups:
            for pattern_name, regex in pattern_list:
                for line_num, line in enumerate(lines, 1):
                    match = regex.search(line)
                    if match:
                        findings.append(
                            Finding(
                                analyzer=self.name,
                                category=category,
                                severity=default_severity,
                                title=f"{pattern_name} detected in {filename}",
                                detail=(
                                    f"Pattern '{pattern_name}' matched"
                                    f" in {filename} at line {line_num}."
                                ),
                                file=filename,
                                line=line_num,
                                evidence=match.group(0)[:200],
                                recommendation=(
                                    f"Review the use of {pattern_name.lower()}"
                                    " in this file."
                                ),
                            )
                        )
                        break  # One finding per pattern per file

        return findings

    def _check_yara(self, content_map: dict[str, str]) -> list[Finding]:
        """Run YARA rules against all content."""
        if not self._yara_rules:
            return []

        findings: list[Finding] = []

        for filename, content in content_map.items():
            try:
                matches = self._yara_rules.match(data=content)
            except yara.Error as e:
                logger.warning("yara_match_error", file=filename, error=str(e))
                continue

            for match in matches:
                meta = match.meta
                category_str = meta.get("category", "")
                severity_str = meta.get("severity", "medium")

                category = _CATEGORY_MAP.get(category_str, Category.MALWARE)
                severity = _SEVERITY_MAP.get(severity_str, Severity.MEDIUM)

                findings.append(
                    Finding(
                        analyzer=self.name,
                        category=category,
                        severity=severity,
                        title=f"YARA: {meta.get('description', match.rule)} in {filename}",
                        detail=(
                            f"YARA rule '{match.rule}' matched"
                            f" in {filename}. {meta.get('description', '')}"
                        ),
                        file=filename,
                        evidence=match.rule,
                        recommendation="Review the flagged content for security implications.",
                    )
                )

        return findings

    def _check_signatures(self, skill: SkillPackage) -> list[Finding]:
        """Check for known malicious publisher identifiers."""
        findings: list[Finding] = []
        author = skill.frontmatter.get("author", "")

        if author in KNOWN_MALICIOUS_PUBLISHERS:
            findings.append(
                Finding(
                    analyzer=self.name,
                    category=Category.MALWARE,
                    severity=Severity.CRITICAL,
                    title=f"Known malicious publisher: {author}",
                    detail=(
                        f"The skill author '{author}' is in the"
                        " known malicious publishers database."
                    ),
                    file="SKILL.md",
                    evidence=author,
                    recommendation="Do not install skills from this publisher.",
                )
            )

        return findings

    def _check_permissions(self, skill: SkillPackage) -> list[Finding]:
        """Check for excessive permission requests."""
        findings: list[Finding] = []
        required_bins = skill.requires.get("bins", [])

        if not isinstance(required_bins, list):
            return findings

        flagged_bins = set(required_bins) & patterns.POWERFUL_BINS
        if flagged_bins:
            findings.append(
                Finding(
                    analyzer=self.name,
                    category=Category.EXCESSIVE_PERMISSIONS,
                    severity=Severity.MEDIUM,
                    title=f"Excessive binary requirements: {', '.join(sorted(flagged_bins))}",
                    detail=(
                        "The skill requires powerful system"
                        " binaries ("
                        f"{', '.join(sorted(flagged_bins))}"
                        ") which may not be appropriate"
                        " for its stated purpose: "
                        f"'{skill.description}'."
                    ),
                    file="SKILL.md",
                    evidence=str(required_bins),
                    recommendation=(
                        "Verify these binaries are truly needed"
                        " for the skill's functionality."
                    ),
                )
            )

        return findings

    def _check_c2_domains(self, content_map: dict[str, str]) -> list[Finding]:
        """Check for known C2 domains in all content."""
        findings: list[Finding] = []

        for filename, content in content_map.items():
            for domain in KNOWN_C2_DOMAINS:
                if domain in content:
                    findings.append(
                        Finding(
                            analyzer=self.name,
                            category=Category.NETWORK_EXFILTRATION,
                            severity=Severity.CRITICAL,
                            title=f"Known C2 domain: {domain} in {filename}",
                            detail=f"The file {filename} references known C2 domain '{domain}'.",
                            file=filename,
                            evidence=domain,
                            recommendation=(
                                "This skill communicates with a"
                                " known malicious server."
                                " Do not install."
                            ),
                        )
                    )

        return findings
