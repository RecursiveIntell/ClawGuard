"""Extract structured content from the markdown body of a SKILL.md."""

import re
from dataclasses import dataclass, field


@dataclass
class MarkdownSection:
    """A section of markdown content defined by a heading."""

    heading: str
    level: int
    content: str


@dataclass
class CodeBlock:
    """A fenced code block extracted from markdown."""

    language: str
    content: str
    line: int  # 1-based line number in the original body


@dataclass
class MarkdownBody:
    """Parsed markdown body with sections, code blocks, and URLs."""

    sections: list[MarkdownSection] = field(default_factory=list)
    code_blocks: list[CodeBlock] = field(default_factory=list)
    urls: list[str] = field(default_factory=list)


_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)
_CODE_BLOCK_RE = re.compile(r"^```(\w*)\n(.*?)^```", re.MULTILINE | re.DOTALL)
_URL_RE = re.compile(r"https?://[^\s\)>\]\"']+")


def parse_markdown(body: str) -> MarkdownBody:
    """Parse a markdown body into sections, code blocks, and URLs."""
    sections = _extract_sections(body)
    code_blocks = _extract_code_blocks(body)
    urls = _extract_urls(body)
    return MarkdownBody(sections=sections, code_blocks=code_blocks, urls=urls)


def _extract_sections(body: str) -> list[MarkdownSection]:
    """Split markdown into sections by heading."""
    headings = list(_HEADING_RE.finditer(body))
    if not headings:
        return [MarkdownSection(heading="", level=0, content=body)] if body.strip() else []

    sections = []

    # Content before the first heading
    pre_content = body[: headings[0].start()].strip()
    if pre_content:
        sections.append(MarkdownSection(heading="", level=0, content=pre_content))

    for i, match in enumerate(headings):
        level = len(match.group(1))
        heading = match.group(2).strip()
        start = match.end()
        end = headings[i + 1].start() if i + 1 < len(headings) else len(body)
        content = body[start:end].strip()
        sections.append(MarkdownSection(heading=heading, level=level, content=content))

    return sections


def _extract_code_blocks(body: str) -> list[CodeBlock]:
    """Extract fenced code blocks with language annotations."""
    blocks = []
    for match in _CODE_BLOCK_RE.finditer(body):
        language = match.group(1) or ""
        content = match.group(2)
        line = body[: match.start()].count("\n") + 1
        blocks.append(CodeBlock(language=language, content=content, line=line))
    return blocks


def _extract_urls(body: str) -> list[str]:
    """Extract all URLs from markdown content."""
    return list(dict.fromkeys(_URL_RE.findall(body)))
