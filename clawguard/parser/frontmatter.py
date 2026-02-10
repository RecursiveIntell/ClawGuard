"""Extract and parse YAML frontmatter from SKILL.md files."""

import structlog
import yaml

logger = structlog.get_logger()

FRONTMATTER_DELIMITER = "---"


def extract_frontmatter(content: str) -> tuple[dict, str]:
    """Extract YAML frontmatter and return (frontmatter_dict, body).

    Frontmatter is the content between the first pair of '---' delimiters
    at the start of the file. If no valid frontmatter is found, returns
    an empty dict and the full content as body.
    """
    stripped = content.lstrip("\n")
    if not stripped.startswith(FRONTMATTER_DELIMITER):
        logger.warning("no_frontmatter_found", reason="file does not start with ---")
        return {}, content

    # Find the closing delimiter
    first_delim_end = stripped.index(FRONTMATTER_DELIMITER) + len(FRONTMATTER_DELIMITER)
    rest = stripped[first_delim_end:]

    # Skip the newline after first ---
    if rest.startswith("\n"):
        rest = rest[1:]

    closing_idx = rest.find(f"\n{FRONTMATTER_DELIMITER}")
    if closing_idx == -1:
        logger.warning("no_frontmatter_found", reason="no closing --- delimiter")
        return {}, content

    yaml_content = rest[:closing_idx]
    body_start = closing_idx + len(f"\n{FRONTMATTER_DELIMITER}")
    body = rest[body_start:]

    # Strip leading newline from body
    if body.startswith("\n"):
        body = body[1:]

    return _parse_yaml(yaml_content), body


def _parse_yaml(yaml_content: str) -> dict:
    """Safely parse YAML content. Returns empty dict on failure."""
    try:
        result = yaml.safe_load(yaml_content)
        if not isinstance(result, dict):
            logger.warning("invalid_frontmatter", reason="YAML did not parse to a dict")
            return {}
        return result
    except yaml.YAMLError as e:
        logger.warning("malformed_yaml", error=str(e))
        return {}
