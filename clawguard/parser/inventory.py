"""Discover and read bundled script files in a skill directory."""

from pathlib import Path

import structlog

from clawguard.config import settings

logger = structlog.get_logger()

LANGUAGE_MAP: dict[str, str] = {
    ".py": "python",
    ".sh": "bash",
    ".bash": "bash",
    ".js": "javascript",
    ".ts": "typescript",
    ".jsx": "javascript",
    ".tsx": "typescript",
    ".md": "markdown",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".json": "json",
    ".toml": "toml",
}

# Files to skip (not useful for analysis)
SKIP_FILES = {".gitignore", ".DS_Store", "Thumbs.db"}


def discover_scripts(skill_dir: Path) -> list[dict]:
    """Discover all files in a skill directory and return their content.

    Returns a list of dicts: {path, content, language}.
    Skips SKILL.md itself, hidden files, and files exceeding MAX_SKILL_SIZE_MB.
    """
    if not skill_dir.is_dir():
        logger.warning("skill_dir_not_found", path=str(skill_dir))
        return []

    max_bytes = settings.MAX_SKILL_SIZE_MB * 1024 * 1024
    scripts = []

    for filepath in sorted(skill_dir.rglob("*")):
        if not filepath.is_file():
            continue

        # Skip SKILL.md, hidden files, and known skip files
        rel_path = filepath.relative_to(skill_dir)
        if rel_path.name == "SKILL.md":
            continue
        if rel_path.name.startswith("."):
            continue
        if rel_path.name in SKIP_FILES:
            continue

        # Check file size
        file_size = filepath.stat().st_size
        if file_size > max_bytes:
            logger.warning(
                "file_too_large",
                path=str(rel_path),
                size_mb=round(file_size / (1024 * 1024), 2),
                max_mb=settings.MAX_SKILL_SIZE_MB,
            )
            continue

        # Read content
        try:
            content = filepath.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError) as e:
            logger.warning("file_read_error", path=str(rel_path), error=str(e))
            continue

        language = LANGUAGE_MAP.get(filepath.suffix.lower(), "unknown")
        scripts.append({
            "path": str(rel_path),
            "content": content,
            "language": language,
        })

    return scripts
