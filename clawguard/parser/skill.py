"""Main entry point for parsing OpenClaw skill packages."""

from pathlib import Path

import structlog

from clawguard.analyzers.base import SkillPackage
from clawguard.exceptions import ParseError
from clawguard.parser.frontmatter import extract_frontmatter
from clawguard.parser.inventory import discover_scripts

logger = structlog.get_logger()


def parse_skill(path: str | Path) -> SkillPackage:
    """Parse a skill directory into a SkillPackage.

    Args:
        path: Path to a skill directory containing SKILL.md.

    Returns:
        Populated SkillPackage dataclass.

    Raises:
        ParseError: If SKILL.md is missing or has no name field.
    """
    skill_dir = Path(path)
    skill_md_path = skill_dir / "SKILL.md"

    if not skill_md_path.exists():
        raise ParseError(f"SKILL.md not found in {skill_dir}")

    raw_content = skill_md_path.read_text(encoding="utf-8")
    frontmatter, instructions = extract_frontmatter(raw_content)

    name = frontmatter.get("name")
    if not name:
        raise ParseError(f"SKILL.md in {skill_dir} is missing required 'name' field")

    description = frontmatter.get("description", "")
    metadata = frontmatter.get("metadata", {})
    requires = frontmatter.get("requires", {})
    install_raw = frontmatter.get("install", [])

    # Normalize install instructions
    install_instructions = []
    if isinstance(install_raw, list):
        for item in install_raw:
            if isinstance(item, dict):
                install_instructions.append(item)
            elif isinstance(item, str):
                install_instructions.append({"command": item, "description": ""})

    scripts = discover_scripts(skill_dir)

    logger.info(
        "skill_parsed",
        name=name,
        path=str(skill_dir),
        scripts_count=len(scripts),
        has_frontmatter=bool(frontmatter),
    )

    return SkillPackage(
        name=name,
        description=description,
        path=str(skill_dir),
        skill_md_raw=raw_content,
        frontmatter=frontmatter,
        instructions=instructions,
        scripts=scripts,
        metadata=metadata,
        requires=requires,
        install_instructions=install_instructions,
    )
