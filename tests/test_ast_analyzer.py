"""Tests for the AST analyzer."""

from clawguard.analyzers.ast_analyzer import ASTAnalyzer
from clawguard.analyzers.base import Category, Finding, Severity, SkillPackage
from clawguard.parser.skill import parse_skill


def _make_skill(scripts=None, **kwargs):
    """Helper to create a minimal SkillPackage for testing."""
    defaults = {
        "name": "test-skill",
        "description": "test",
        "path": "/tmp/test",
        "skill_md_raw": "---\nname: test\n---\n# Test",
        "frontmatter": {"name": "test"},
        "instructions": "# Test",
        "scripts": scripts or [],
    }
    defaults.update(kwargs)
    return SkillPackage(**defaults)


class TestASTAnalyzer:
    def setup_method(self):
        self.analyzer = ASTAnalyzer()

    def test_name(self):
        assert self.analyzer.name == "ast"

    def test_supports_with_scripts(self):
        skill = _make_skill(scripts=[{"path": "test.py", "content": "", "language": "python"}])
        assert self.analyzer.supports(skill) is True

    def test_supports_without_scripts(self):
        skill = _make_skill(scripts=[])
        assert self.analyzer.supports(skill) is False

    def test_detects_eval(self):
        skill = _make_skill(scripts=[{
            "path": "evil.py",
            "content": "data = eval(input())\n",
            "language": "python",
        }])
        findings = self.analyzer.analyze(skill)
        assert any(
            "eval" in f.title and f.category == Category.OBFUSCATION
            for f in findings
        )

    def test_detects_exec(self):
        skill = _make_skill(scripts=[{
            "path": "evil.py",
            "content": "exec(code)\n",
            "language": "python",
        }])
        findings = self.analyzer.analyze(skill)
        assert any("exec" in f.title for f in findings)

    def test_detects_os_system(self):
        skill = _make_skill(scripts=[{
            "path": "run.py",
            "content": "import os\nos.system('ls')\n",
            "language": "python",
        }])
        findings = self.analyzer.analyze(skill)
        assert any("os.system" in f.title for f in findings)

    def test_detects_subprocess(self):
        skill = _make_skill(scripts=[{
            "path": "run.py",
            "content": "import subprocess\nsubprocess.call(['ls'])\n",
            "language": "python",
        }])
        findings = self.analyzer.analyze(skill)
        assert any("subprocess" in f.title for f in findings)

    def test_detects_dunder_import(self):
        skill = _make_skill(scripts=[{
            "path": "loader.py",
            "content": "mod = __import__('os')\n",
            "language": "python",
        }])
        findings = self.analyzer.analyze(skill)
        assert any("__import__" in f.title for f in findings)

    def test_obfuscated_payload_fixture(self, fixtures_dir):
        """Should catch base64 decode -> exec in helper.py."""
        skill = parse_skill(fixtures_dir / "obfuscated_payload")
        findings = self.analyzer.analyze(skill)
        # Should find exec() and compile() calls
        titles = [f.title for f in findings]
        assert any("exec" in t or "compile" in t for t in titles)

    def test_supply_chain_timebomb_fixture(self, fixtures_dir):
        """Should catch remote import pattern in loader.py."""
        skill = parse_skill(fixtures_dir / "supply_chain_timebomb")
        findings = self.analyzer.analyze(skill)
        # Should find exec(), compile(), or urllib usage
        assert len(findings) > 0

    def test_clean_complex_skill_minimal(self, fixtures_dir):
        """Clean complex skill should have minimal AST findings."""
        skill = parse_skill(fixtures_dir / "clean_complex_skill")
        findings = self.analyzer.analyze(skill)
        # utils.py has no dangerous calls
        critical = [f for f in findings if f.severity == Severity.CRITICAL]
        assert len(critical) == 0

    def test_bash_sudo_detected(self):
        skill = _make_skill(scripts=[{
            "path": "setup.sh",
            "content": "#!/bin/bash\nsudo apt install curl\n",
            "language": "bash",
        }])
        findings = self.analyzer.analyze(skill)
        assert any(
            "sudo" in f.title and f.category == Category.EXCESSIVE_PERMISSIONS
            for f in findings
        )

    def test_bash_env_dump_detected(self):
        skill = _make_skill(scripts=[{
            "path": "setup.sh",
            "content": '#!/bin/bash\nenv > /tmp/envdump.txt\n',
            "language": "bash",
        }])
        findings = self.analyzer.analyze(skill)
        assert any(
            f.category == Category.CREDENTIAL_EXPOSURE
            for f in findings
        )

    def test_findings_have_line_numbers(self):
        skill = _make_skill(scripts=[{
            "path": "evil.py",
            "content": "x = 1\ny = eval('1+1')\n",
            "language": "python",
        }])
        findings = self.analyzer.analyze(skill)
        eval_findings = [f for f in findings if "eval" in f.title]
        assert len(eval_findings) == 1
        assert eval_findings[0].line == 2

    def test_findings_are_finding_instances(self):
        skill = _make_skill(scripts=[{
            "path": "evil.py",
            "content": "eval('x')\n",
            "language": "python",
        }])
        findings = self.analyzer.analyze(skill)
        assert all(isinstance(f, Finding) for f in findings)
        assert all(f.analyzer == "ast" for f in findings)

    def test_malicious_credential_harvester_bash(self, fixtures_dir):
        """Should detect dangerous commands in setup.sh."""
        skill = parse_skill(fixtures_dir / "malicious_credential_harvester")
        findings = self.analyzer.analyze(skill)
        assert len(findings) > 0
