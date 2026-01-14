"""Command-line interface for Named."""

from pathlib import Path

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from named import __version__
from named.logging import configure_logging, get_logger

logger = get_logger("cli")

app = typer.Typer(
    name="named",
    help="Intelligent Java code refactoring system for naming conventions.",
    add_completion=False,
)
console = Console()


def version_callback(value: bool):
    """Show version and exit."""
    if value:
        console.print(f"[bold]named[/bold] version {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool | None = typer.Option(
        None,
        "--version",
        "-v",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit.",
    ),
):
    """Named - Intelligent Java code refactoring system."""
    pass


@app.command()
def analyze(
    path: Path = typer.Argument(
        ...,
        help="Path to Java project directory or single Java file.",
        exists=True,
    ),
    output: Path = typer.Option(
        Path("./named-report"),
        "--output",
        "-o",
        help="Output directory for reports.",
    ),
    format: str = typer.Option(
        "all",
        "--format",
        "-f",
        help="Output format: json, md, or all.",
    ),
    model: str = typer.Option(
        "gpt-4o",
        "--model",
        "-m",
        help="OpenAI model to use.",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Only parse and show statistics, don't call LLM.",
    ),
    exclude: list[str] | None = typer.Option(
        None,
        "--exclude",
        "-e",
        help="Glob patterns to exclude (e.g., '**/test/**').",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show detailed progress and LLM prompts/responses.",
    ),
):
    """Analyze Java code and generate naming improvement suggestions.

    This command parses Java files, analyzes naming conventions using AI,
    and generates a report with suggestions for improvements.

    Examples:
        named analyze ./my-project
        named analyze ./src/Main.java --output ./report
        named analyze ./project --format json --exclude "**/test/**"
    """
    # Configure logging based on verbose flag
    configure_logging(verbose=verbose)
    logger.debug(f"Starting analysis of {path}")

    console.print("\n[bold blue]Named[/bold blue] - Java Naming Analysis\n")

    # Validate format
    if format not in ("json", "md", "all"):
        console.print(f"[red]Error:[/red] Invalid format '{format}'. Use: json, md, or all")
        raise typer.Exit(1)

    # Check if path is file or directory
    if path.is_file():
        if not path.suffix == ".java":
            console.print(f"[red]Error:[/red] Not a Java file: {path}")
            raise typer.Exit(1)
        java_files = [path]
        project_path = path.parent
    else:
        project_path = path
        # Find Java files
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            progress.add_task("Finding Java files...", total=None)
            from named.analysis.parser import find_java_files

            java_files = find_java_files(path, exclude)

    if not java_files:
        console.print(f"[yellow]Warning:[/yellow] No Java files found in {path}")
        raise typer.Exit(0)

    console.print(f"Found [bold]{len(java_files)}[/bold] Java file(s)\n")

    # Parse and extract symbols
    all_symbols = []
    parse_errors = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Parsing Java files...", total=len(java_files))

        from named.analysis.extractor import extract_symbols
        from named.analysis.parser import JavaParseError

        for java_file in java_files:
            try:
                symbols = extract_symbols(java_file)
                all_symbols.extend(symbols)
            except JavaParseError as e:
                parse_errors.append(str(e))
            except Exception as e:
                parse_errors.append(f"{java_file}: {e}")
            progress.advance(task)

    # Show parsing summary
    console.print(f"\nExtracted [bold]{len(all_symbols)}[/bold] symbols")

    if parse_errors:
        console.print(f"[yellow]Warning:[/yellow] {len(parse_errors)} file(s) had parse errors")
        for error in parse_errors[:5]:  # Show first 5 errors
            console.print(f"  - {error}")
        if len(parse_errors) > 5:
            console.print(f"  ... and {len(parse_errors) - 5} more")

    # Show symbol breakdown
    _show_symbol_summary(all_symbols)

    if dry_run:
        console.print("\n[yellow]Dry run mode:[/yellow] Skipping LLM analysis")
        raise typer.Exit(0)

    # Pre-filter blocked symbols
    from named.validation.validator import pre_filter_symbols

    analyzable, blocked = pre_filter_symbols(all_symbols)

    console.print("\n[bold]Analysis:[/bold]")
    console.print(f"  - Analyzable symbols: {len(analyzable)}")
    console.print(f"  - Blocked by guardrails: {len(blocked)}")

    if not analyzable:
        console.print("\n[yellow]No symbols to analyze after guardrail filtering.[/yellow]")
        raise typer.Exit(0)

    # Analyze with LLM
    results = []

    try:
        from rich.progress import BarColumn, TaskProgressColumn, TimeRemainingColumn

        from named.suggestions.llm_client import LLMClient, LLMError
        from named.validation.validator import validate_suggestion

        client = LLMClient(model=model, verbose=verbose)

        # Group symbols by file for better progress display
        symbols_by_file: dict[Path, list] = {}
        for symbol in analyzable:
            file_path = symbol.location.file
            if file_path not in symbols_by_file:
                symbols_by_file[file_path] = []
            symbols_by_file[file_path].append(symbol)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeRemainingColumn(),
            console=console,
        ) as progress:
            task = progress.add_task(
                f"Analyzing with {model}...",
                total=len(analyzable),
            )

            symbol_count = 0
            for file_path, file_symbols in symbols_by_file.items():
                # Show current file being analyzed
                file_name = file_path.name

                for symbol in file_symbols:
                    symbol_count += 1

                    # Update progress with current file and symbol
                    progress.update(
                        task,
                        description=f"[cyan]{file_name}[/cyan]: {symbol.kind} [bold]{symbol.name}[/bold]",
                    )

                    if verbose:
                        console.print(
                            f"\n[dim]Analyzing {symbol_count}/{len(analyzable)}: {file_name}:{symbol.name} ({symbol.kind})[/dim]"
                        )

                    try:
                        suggestion = client.analyze_symbol(
                            symbol_name=symbol.name,
                            symbol_kind=symbol.kind,
                            annotations=symbol.annotations,
                            context=symbol.context,
                        )

                        if suggestion:
                            # Find references for this symbol
                            from named.analysis.reference_finder import find_references

                            refs = find_references(
                                symbol_name=symbol.name,
                                symbol_kind=symbol.kind,
                                java_files=java_files,
                                parent_class=symbol.parent_class,
                            )
                            suggestion.references = refs
                            suggestion.location = {
                                "file": str(symbol.location.file),
                                "line": symbol.location.line,
                            }

                            # Compute impact analysis (always, even for zero references)
                            from named.analysis.impact_analyzer import compute_rename_impact

                            suggestion.impact_analysis = compute_rename_impact(refs)

                            result = validate_suggestion(suggestion, symbol.annotations)
                            results.append(result)

                            if verbose and suggestion.suggested_name:
                                ref_count = len(refs)
                                console.print(
                                    f"  [green]→ Suggestion:[/green] {symbol.name} → {suggestion.suggested_name} ({suggestion.confidence:.0%}) [dim]({ref_count} refs)[/dim]"
                                )

                    except LLMError as e:
                        console.print(
                            f"\n[yellow]Warning:[/yellow] Failed to analyze {symbol.name}: {e}"
                        )

                    progress.advance(task)

    except LLMError as e:
        console.print(f"\n[red]Error:[/red] LLM client error: {e}")
        console.print("\nMake sure NAMED_OPENAI_API_KEY environment variable is set.")
        raise typer.Exit(1)

    # Generate reports
    console.print("\n[bold]Generating reports...[/bold]")

    output.mkdir(parents=True, exist_ok=True)

    if format in ("json", "all"):
        from named.export.json_exporter import export_json

        json_path = export_json(results, all_symbols, output, project_path, model)
        console.print(f"  - JSON: {json_path}")

    if format in ("md", "all"):
        from named.export.markdown_exporter import export_markdown

        md_path = export_markdown(results, all_symbols, output, project_path, model)
        console.print(f"  - Markdown: {md_path}")

    # Show results summary
    _show_results_summary(results)

    console.print("\n[bold green]Analysis complete![/bold green]")
    console.print(f"Reports saved to: {output.absolute()}\n")


def _show_symbol_summary(symbols):
    """Show a summary table of extracted symbols."""
    from collections import Counter

    kinds = Counter(s.kind for s in symbols)

    table = Table(title="Symbol Breakdown")
    table.add_column("Kind", style="cyan")
    table.add_column("Count", justify="right")

    for kind, count in sorted(kinds.items()):
        table.add_row(kind, str(count))

    console.print(table)


def _show_results_summary(results):
    """Show a summary of analysis results."""
    if not results:
        console.print("\n[yellow]No suggestions generated.[/yellow]")
        return

    valid = sum(1 for r in results if r.is_valid)
    blocked = sum(1 for r in results if r.suggestion.blocked)
    high_conf = sum(1 for r in results if r.suggestion.confidence >= 0.85)

    console.print("\n[bold]Results Summary:[/bold]")
    console.print(f"  - Total suggestions: {len(results)}")
    console.print(f"  - Valid suggestions: {valid}")
    console.print(f"  - Blocked by guardrails: {blocked}")
    console.print(f"  - High confidence (>=85%): {high_conf}")

    # Show top 5 suggestions
    top_suggestions = sorted(
        [r for r in results if r.is_valid],
        key=lambda r: -r.suggestion.confidence,
    )[:5]

    if top_suggestions:
        console.print("\n[bold]Top Suggestions:[/bold]")
        for result in top_suggestions:
            s = result.suggestion
            console.print(
                f"  [cyan]{s.original_name}[/cyan] → "
                f"[green]{s.suggested_name}[/green] "
                f"({s.confidence:.0%})"
            )


@app.command()
def rules(
    lang: str = typer.Option(
        "en",
        "--lang",
        "-l",
        help="Language for rule descriptions: en or es.",
    ),
):
    """Show all naming rules and guardrails.

    This command displays the 9 naming rules and 4 guardrails
    that Named uses to analyze Java code.
    """
    from named.rules.guardrails import GUARDRAILS
    from named.rules.naming_rules import NAMING_RULES

    console.print("\n[bold blue]Named[/bold blue] - Naming Rules\n")

    # Show rules
    console.print("[bold]9 Naming Rules:[/bold]\n")

    for rule in NAMING_RULES:
        name = rule.name_en if lang == "en" else rule.name
        desc = rule.description_en if lang == "en" else rule.description
        severity = (
            "[red]ERROR[/red]" if rule.severity.value == "error" else "[yellow]WARNING[/yellow]"
        )

        console.print(f"[bold cyan]{rule.id}[/bold cyan]: {name}")
        console.print(f"  {severity} | {rule.category.value}")
        console.print(f"  {desc}")
        console.print(f"  Good: {', '.join(rule.examples_good[:3])}")
        console.print(f"  Bad: {', '.join(rule.examples_bad[:3])}")
        console.print()

    # Show guardrails
    console.print("[bold]4 Guardrails (Blocking Conditions):[/bold]\n")

    for guardrail in GUARDRAILS:
        name = guardrail.name_en if lang == "en" else guardrail.name
        desc = guardrail.description_en if lang == "en" else guardrail.description

        console.print(f"[bold red]{guardrail.id}[/bold red]: {name}")
        console.print(f"  {desc}")
        if guardrail.blocked_annotations:
            console.print(
                f"  Blocked annotations: {', '.join(f'@{a}' for a in guardrail.blocked_annotations[:5])}"
            )
        if guardrail.threshold:
            console.print(f"  Threshold: {guardrail.threshold}")
        console.print()


if __name__ == "__main__":
    app()
