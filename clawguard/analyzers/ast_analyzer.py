"""AST analyzer — tree-sitter-based analysis of bundled scripts."""

import structlog
import tree_sitter_bash as tsbash
import tree_sitter_python as tspython
from tree_sitter import Language, Parser

from clawguard.analyzers.base import (
    AnalyzerBase,
    Category,
    Finding,
    Severity,
    SkillPackage,
)

logger = structlog.get_logger()

# Dangerous Python function calls
DANGEROUS_PYTHON_CALLS = {
    "eval": (Category.OBFUSCATION, Severity.HIGH, "eval() can execute arbitrary code"),
    "exec": (Category.OBFUSCATION, Severity.HIGH, "exec() can execute arbitrary code"),
    "compile": (Category.OBFUSCATION, Severity.MEDIUM, "compile() can prepare code for execution"),
    "__import__": (
        Category.SUPPLY_CHAIN,
        Severity.HIGH,
        "Dynamic import can load arbitrary modules",
    ),
}

# Dangerous Python attribute calls (module.func patterns)
DANGEROUS_PYTHON_ATTR_CALLS = {
    ("subprocess", "call"): (
        Category.SUPPLY_CHAIN,
        Severity.MEDIUM,
        "subprocess.call can run shell commands",
    ),
    ("subprocess", "run"): (
        Category.SUPPLY_CHAIN,
        Severity.MEDIUM,
        "subprocess.run can run shell commands",
    ),
    ("subprocess", "Popen"): (
        Category.SUPPLY_CHAIN,
        Severity.HIGH,
        "subprocess.Popen can spawn processes",
    ),
    ("subprocess", "check_output"): (
        Category.SUPPLY_CHAIN,
        Severity.MEDIUM,
        "subprocess.check_output runs shell commands",
    ),
    ("os", "system"): (Category.SUPPLY_CHAIN, Severity.HIGH, "os.system executes shell commands"),
    ("os", "popen"): (Category.SUPPLY_CHAIN, Severity.HIGH, "os.popen executes shell commands"),
    ("os", "dup2"): (
        Category.MALWARE,
        Severity.CRITICAL,
        "os.dup2 is used in reverse shell payloads",
    ),
    ("importlib", "import_module"): (
        Category.SUPPLY_CHAIN,
        Severity.MEDIUM,
        "Dynamic module import",
    ),
    ("urllib", "request"): (
        Category.NETWORK_EXFILTRATION,
        Severity.MEDIUM,
        "URL request may fetch remote code",
    ),
}

# Bash commands that indicate privilege escalation or data exfiltration
DANGEROUS_BASH_COMMANDS = {
    "sudo": (Category.EXCESSIVE_PERMISSIONS, Severity.HIGH, "Privilege escalation via sudo"),
    "chown": (Category.EXCESSIVE_PERMISSIONS, Severity.MEDIUM, "File ownership change"),
    "env": (Category.CREDENTIAL_EXPOSURE, Severity.MEDIUM, "Environment dump"),
    "printenv": (Category.CREDENTIAL_EXPOSURE, Severity.MEDIUM, "Environment dump"),
}


def _build_parser(language_obj: object) -> Parser | None:
    """Build a tree-sitter parser for the given language."""
    try:
        lang = Language(language_obj)
        parser = Parser(lang)
        return parser
    except Exception as e:
        logger.warning("tree_sitter_init_failed", error=str(e))
        return None


class ASTAnalyzer(AnalyzerBase):
    """AST-based analyzer using tree-sitter for Python and Bash scripts."""

    def __init__(self) -> None:
        self._python_parser = _build_parser(tspython.language())
        self._bash_parser = _build_parser(tsbash.language())

    @property
    def name(self) -> str:
        return "ast"

    def supports(self, skill: SkillPackage) -> bool:
        """Only run on skills that have bundled scripts."""
        return len(skill.scripts) > 0

    def analyze(self, skill: SkillPackage) -> list[Finding]:
        """Run AST analysis on all bundled scripts."""
        findings: list[Finding] = []

        for script in skill.scripts:
            lang = script["language"]
            content = script["content"]
            path = script["path"]

            if lang == "python" and self._python_parser:
                findings.extend(self._analyze_python(path, content))
            elif lang == "bash" and self._bash_parser:
                findings.extend(self._analyze_bash(path, content))

        return findings

    def _analyze_python(self, filepath: str, content: str) -> list[Finding]:
        """Analyze a Python script using tree-sitter AST."""
        findings: list[Finding] = []
        tree = self._python_parser.parse(content.encode())
        root = tree.root_node

        self._walk_python_node(root, filepath, content, findings)
        return findings

    def _walk_python_node(
        self,
        node: object,
        filepath: str,
        content: str,
        findings: list[Finding],
    ) -> None:
        """Recursively walk the Python AST looking for dangerous patterns."""
        if node.type == "call":
            self._check_python_call(node, filepath, content, findings)

        for child in node.children:
            self._walk_python_node(child, filepath, content, findings)

    def _check_python_call(
        self,
        node: object,
        filepath: str,
        content: str,
        findings: list[Finding],
    ) -> None:
        """Check a Python function call node for dangerous patterns."""
        func_node = node.child_by_field_name("function")
        if not func_node:
            return

        line = node.start_point[0] + 1

        # Direct function calls: eval(), exec(), compile(), __import__()
        if func_node.type == "identifier":
            func_name = func_node.text.decode()
            if func_name in DANGEROUS_PYTHON_CALLS:
                cat, sev, desc = DANGEROUS_PYTHON_CALLS[func_name]
                findings.append(
                    Finding(
                        analyzer=self.name,
                        category=cat,
                        severity=sev,
                        title=f"Dangerous call: {func_name}() in {filepath}",
                        detail=f"{desc}. Found at line {line} in {filepath}.",
                        file=filepath,
                        line=line,
                        evidence=content.splitlines()[line - 1].strip()[:200]
                        if line <= len(content.splitlines())
                        else "",
                        recommendation=(
                            f"Avoid using {func_name}()"
                            " — especially with untrusted input."
                        ),
                    )
                )

        # Attribute calls: os.system(), subprocess.call(), etc.
        elif func_node.type == "attribute":
            obj_node = func_node.child_by_field_name("object")
            attr_node = func_node.child_by_field_name("attribute")
            if obj_node and attr_node:
                obj_name = obj_node.text.decode()
                attr_name = attr_node.text.decode()
                key = (obj_name, attr_name)
                if key in DANGEROUS_PYTHON_ATTR_CALLS:
                    cat, sev, desc = DANGEROUS_PYTHON_ATTR_CALLS[key]
                    findings.append(
                        Finding(
                            analyzer=self.name,
                            category=cat,
                            severity=sev,
                            title=f"Dangerous call: {obj_name}.{attr_name}() in {filepath}",
                            detail=f"{desc}. Found at line {line} in {filepath}.",
                            file=filepath,
                            line=line,
                            evidence=content.splitlines()[line - 1].strip()[:200]
                            if line <= len(content.splitlines())
                            else "",
                            recommendation=f"Review the use of {obj_name}.{attr_name}().",
                        )
                    )

    def _analyze_bash(self, filepath: str, content: str) -> list[Finding]:
        """Analyze a Bash script using tree-sitter AST."""
        findings: list[Finding] = []
        tree = self._bash_parser.parse(content.encode())
        root = tree.root_node

        self._walk_bash_node(root, filepath, content, findings)
        return findings

    def _walk_bash_node(
        self,
        node: object,
        filepath: str,
        content: str,
        findings: list[Finding],
    ) -> None:
        """Recursively walk the Bash AST looking for dangerous patterns."""
        if node.type == "command":
            self._check_bash_command(node, filepath, content, findings)
        elif node.type == "pipeline":
            self._check_bash_pipeline(node, filepath, content, findings)

        for child in node.children:
            self._walk_bash_node(child, filepath, content, findings)

    def _check_bash_command(
        self,
        node: object,
        filepath: str,
        content: str,
        findings: list[Finding],
    ) -> None:
        """Check a Bash command node for dangerous patterns."""
        cmd_name_node = node.child_by_field_name("name")
        if not cmd_name_node:
            return

        cmd_name = cmd_name_node.text.decode()
        line = node.start_point[0] + 1

        if cmd_name in DANGEROUS_BASH_COMMANDS:
            cat, sev, desc = DANGEROUS_BASH_COMMANDS[cmd_name]
            findings.append(
                Finding(
                    analyzer=self.name,
                    category=cat,
                    severity=sev,
                    title=f"Dangerous command: {cmd_name} in {filepath}",
                    detail=f"{desc}. Found at line {line} in {filepath}.",
                    file=filepath,
                    line=line,
                    evidence=content.splitlines()[line - 1].strip()[:200]
                    if line <= len(content.splitlines())
                    else "",
                    recommendation=(
                        f"Verify that '{cmd_name}' is necessary"
                        " for this skill's operation."
                    ),
                )
            )

    def _check_bash_pipeline(
        self,
        node: object,
        filepath: str,
        content: str,
        findings: list[Finding],
    ) -> None:
        """Check for dangerous pipe patterns like curl | bash."""
        line = node.start_point[0] + 1
        pipe_text = node.text.decode()

        # Check for curl/wget piped to shell
        commands = [child for child in node.children if child.type == "command"]
        if len(commands) >= 2:
            first_cmd = commands[0].child_by_field_name("name")
            last_cmd = commands[-1].child_by_field_name("name")

            if first_cmd and last_cmd:
                first_name = first_cmd.text.decode()
                last_name = last_cmd.text.decode()

                if first_name in ("curl", "wget") and last_name in ("bash", "sh", "sudo"):
                    findings.append(
                        Finding(
                            analyzer=self.name,
                            category=Category.SOCIAL_ENGINEERING,
                            severity=Severity.CRITICAL,
                            title=f"Pipe to shell: {first_name} | {last_name} in {filepath}",
                            detail=f"Remote content piped directly to shell at line {line}.",
                            file=filepath,
                            line=line,
                            evidence=pipe_text[:200],
                            recommendation=(
                                "Never pipe remote content directly"
                                " to a shell interpreter."
                            ),
                        )
                    )
