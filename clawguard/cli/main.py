"""ClawGuard CLI — security scanner for AI agent skills."""

import logging
import sys
from pathlib import Path

import click
import structlog
from rich.console import Console
from rich.table import Table

from clawguard.analyzers.base import Severity
from clawguard.clawhub.client import ClawHubClient
from clawguard.pipeline import ScanOptions, ScanPipeline
from clawguard.reports.json_report import to_json

# Use stderr for rich output so stdout stays clean for --json/--quiet
console = Console(stderr=True)

# Configure structlog to write to stderr via stdlib logging
logging.basicConfig(format="%(message)s", stream=sys.stderr, level=logging.WARNING)
structlog.configure(
    wrapper_class=structlog.make_filtering_bound_logger(logging.WARNING),
)

_EXIT_CODES = {"PASS": 0, "CAUTION": 1, "REVIEW": 2, "BLOCK": 3}

_SEVERITY_STYLES = {
    Severity.CRITICAL: ("bold red", "\U0001f534"),
    Severity.HIGH: ("bold yellow", "\U0001f7e0"),
    Severity.MEDIUM: ("yellow", "\U0001f7e1"),
    Severity.LOW: ("cyan", "\U0001f535"),
    Severity.INFO: ("dim", "\u2139\ufe0f"),
}


def _recommendation_style(rec: str) -> str:
    return {
        "PASS": "bold green",
        "CAUTION": "bold yellow",
        "REVIEW": "bold red",
        "BLOCK": "bold white on red",
    }.get(rec, "bold")


def _print_report(report, verbose: bool = False) -> None:
    """Print a rich-formatted scan report to the console."""
    console.print()
    console.print(f"[bold]\U0001f50d Scanning: {report.skill.name}[/bold]")
    console.print("\u2501" * 35)

    for analyzer in report.analyzers_run:
        count = sum(1 for f in report.findings if f.analyzer == analyzer)
        console.print(
            f"  {analyzer:<18} \u2705 {count} finding{'s' if count != 1 else ''}"
        )

    console.print("\u2501" * 35)
    console.print()

    rec_style = _recommendation_style(report.score.recommendation)
    console.print(
        f"[bold]Trust Score:[/bold] {report.score.score}/100 "
        f"({report.score.grade}) \u2014 "
        f"[{rec_style}]{report.score.recommendation}[/{rec_style}]"
    )
    console.print()

    for finding in sorted(
        report.findings,
        key=lambda f: list(Severity).index(f.severity),
    ):
        style, icon = _SEVERITY_STYLES.get(finding.severity, ("", ""))
        console.print(
            f"{icon} [{style}]{finding.severity.value.upper()}[/{style}]: "
            f"{finding.title} ({finding.category.value})"
        )
        if finding.file:
            loc = f"   File: {finding.file}"
            if finding.line:
                loc += f", Line: {finding.line}"
            console.print(f"[dim]{loc}[/dim]")
        if finding.recommendation:
            console.print(f"[dim]   \u2192 {finding.recommendation}[/dim]")
        if verbose and finding.evidence:
            console.print(f"[dim]   Evidence: {finding.evidence}[/dim]")
        console.print()


def _write_output(content: str, output: str | None) -> None:
    """Write content to a file or stdout."""
    if output:
        Path(output).write_text(content, encoding="utf-8")
        console.print(f"[green]Report written to {output}[/green]")
    else:
        click.echo(content)


@click.group()
@click.version_option(package_name="clawguard")
def cli() -> None:
    """ClawGuard — Security scanner for AI agent skills."""


@cli.command()
@click.argument("path", required=False)
@click.option("--url", help="ClawHub skill URL to scan.")
@click.option(
    "--json", "json_output", is_flag=True,
    help="Output JSON instead of formatted text.",
)
@click.option("--no-llm", is_flag=True, help="Skip LLM analysis (faster, free).")
@click.option("--output", "-o", help="Write report to file.")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output.")
@click.option("--quiet", "-q", is_flag=True, help="Only output score and recommendation.")
@click.pass_context
def scan(
    ctx: click.Context,
    path: str | None,
    url: str | None,
    json_output: bool,
    no_llm: bool,
    output: str | None,
    verbose: bool,
    quiet: bool,
) -> None:
    """Scan a local skill directory or ClawHub URL."""
    if not path and not url:
        raise click.UsageError("Provide a PATH or --url to scan.")

    options = ScanOptions(skip_llm=no_llm)
    pipeline = ScanPipeline(options=options)

    if url:
        client = ClawHubClient()
        try:
            local_path = client.download(url)
            report = pipeline.scan(local_path)
        finally:
            client.cleanup()
    else:
        report = pipeline.scan(path)

    if json_output:
        _write_output(to_json(report), output)
    elif quiet:
        line = f"{report.score.recommendation} {report.score.score}"
        _write_output(line, output)
    else:
        if output:
            from clawguard.reports.markdown_report import to_markdown

            _write_output(to_markdown(report), output)
        else:
            _print_report(report, verbose=verbose)

    ctx.exit(_EXIT_CODES.get(report.score.recommendation, 1))


@cli.command("scan-all")
@click.argument("directory")
@click.option("--json", "json_output", is_flag=True, help="Output JSON.")
@click.option("--no-llm", is_flag=True, help="Skip LLM analysis.")
@click.option("--quiet", "-q", is_flag=True, help="Only output scores.")
@click.pass_context
def scan_all(
    ctx: click.Context,
    directory: str,
    json_output: bool,
    no_llm: bool,
    quiet: bool,
) -> None:
    """Scan all skill directories under DIRECTORY."""
    base = Path(directory)
    if not base.is_dir():
        raise click.UsageError(f"Not a directory: {directory}")

    options = ScanOptions(skip_llm=no_llm)
    pipeline = ScanPipeline(options=options)

    skill_dirs = sorted(
        d for d in base.iterdir()
        if d.is_dir() and (d / "SKILL.md").exists()
    )

    if not skill_dirs:
        console.print("[yellow]No skill directories found.[/yellow]")
        ctx.exit(0)
        return

    worst_exit = 0
    results = []

    for skill_dir in skill_dirs:
        report = pipeline.scan(skill_dir)
        exit_code = _EXIT_CODES.get(report.score.recommendation, 1)
        worst_exit = max(worst_exit, exit_code)

        if json_output:
            from clawguard.reports.json_report import report_to_dict

            results.append(report_to_dict(report))
        elif quiet:
            click.echo(
                f"{report.score.recommendation} {report.score.score} "
                f"{report.skill.name}"
            )
        else:
            _print_report(report)

    if json_output:
        import json

        click.echo(json.dumps(results, indent=2, default=str))

    ctx.exit(worst_exit)


@cli.command()
@click.argument("directory")
@click.option("--no-llm", is_flag=True, help="Skip LLM analysis.")
def watch(directory: str, no_llm: bool) -> None:
    """Watch a skill directory and re-scan on changes."""
    import time

    skill_path = Path(directory)
    if not skill_path.is_dir():
        raise click.UsageError(f"Not a directory: {directory}")

    options = ScanOptions(skip_llm=no_llm)
    pipeline = ScanPipeline(options=options)

    console.print(f"[bold]Watching {directory} for changes...[/bold]")
    console.print("[dim]Press Ctrl+C to stop.[/dim]")

    last_mtime: float = 0

    try:
        while True:
            current_mtime = max(
                (f.stat().st_mtime for f in skill_path.rglob("*") if f.is_file()),
                default=0,
            )
            if current_mtime > last_mtime:
                last_mtime = current_mtime
                console.clear()
                report = pipeline.scan(skill_path)
                _print_report(report)
            time.sleep(1)
    except KeyboardInterrupt:
        console.print("\n[dim]Stopped watching.[/dim]")


@cli.command("bulk-scan")
@click.option("--limit", default=100, help="Number of skills to scan.")
@click.option("--json", "json_output", is_flag=True, help="Output JSON.")
def bulk_scan(limit: int, json_output: bool) -> None:
    """Scan top N skills from the ClawHub registry."""
    from clawguard.clawhub.bulk import BulkScanProgress
    from clawguard.clawhub.bulk import bulk_scan as do_bulk_scan

    def progress(p: BulkScanProgress) -> None:
        console.print(
            f"[dim][{p.current}/{p.total}] Scanning {p.skill_name}...[/dim]"
        )

    results = do_bulk_scan(limit=limit, progress_callback=progress)

    if json_output:
        import json

        click.echo(json.dumps(results, indent=2, default=str))
    else:
        table = Table(title=f"ClawHub Bulk Scan ({len(results)} skills)")
        table.add_column("Skill", style="bold")
        table.add_column("Score", justify="right")
        table.add_column("Grade", justify="center")
        table.add_column("Recommendation")
        table.add_column("Error", style="red")

        for r in results:
            score = str(r["score"]) if r["score"] is not None else "-"
            grade = r["grade"] or "-"
            rec = r["recommendation"] or "-"
            error = r["error"] or ""
            table.add_row(r["name"], score, grade, rec, error)

        console.print(table)
