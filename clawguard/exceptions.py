"""ClawGuard exception hierarchy."""


class ClawGuardError(Exception):
    """Base exception for all ClawGuard errors."""


class ParseError(ClawGuardError):
    """Error parsing a SKILL.md file or skill package."""


class AnalysisError(ClawGuardError):
    """Error during security analysis."""


class ScoringError(ClawGuardError):
    """Error computing trust score."""


class ClawHubError(ClawGuardError):
    """Error communicating with ClawHub."""
