"""Command-line interface for Named."""

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from named import __version__
from named.logging import configure_logging, get_logger

logger = get_logger("cli")

# Pricing per 1M tokens (input, output) in USD
MODEL_PRICING = {
    "gpt-4o": {
        "streaming": {"input": 5.00, "output": 15.00},
        "batch": {"input": 2.50, "output": 7.50},
    },
    "gpt-4o-mini": {
        "streaming": {"input": 0.15, "output": 0.60},
        "batch": {"input": 0.075, "output": 0.30},
    },
}

app = typer.Typer(
    name="named",
    help="Intelligent Java code refactoring system for naming conventions.",
    add_completion=False,
)
console = Console()


@app.callback()
def main():
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
    mode: str = typer.Option(
        "streaming",
        "--mode",
        help="Processing mode: streaming (realtime) or batch (async, 24h, 50%% cost)",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Only parse and show statistics, don't call LLM.",
    ),
    exclude: Optional[list[str]] = typer.Option(
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
        named analyze ./project --mode batch  # Async batch processing (50% cost, 24h)
    """
    # Configure logging based on verbose flag
    configure_logging(verbose=verbose)
    logger.debug(f"Starting analysis of {path}")

    console.print("\n[bold blue]Named[/bold blue] - Java Naming Analysis\n")

    # Validate format
    if format not in ("json", "md", "all"):
        console.print(f"[red]Error:[/red] Invalid format '{format}'. Use: json, md, or all")
        raise typer.Exit(1)

    # Validate mode
    if mode not in ("streaming", "batch"):
        console.print(f"[red]Error:[/red] Invalid mode '{mode}'. Use: streaming or batch")
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

    # Check if batch mode
    if mode == "batch":
        _handle_batch_mode(
            analyzable=analyzable,
            all_symbols=all_symbols,
            java_files=java_files,
            output=output,
            project_path=project_path,
            model=model,
        )
        return

    # Analyze with LLM (streaming mode)
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


@app.command()
def estimate(
    path: Path = typer.Argument(
        ...,
        help="Path to Java project directory or single Java file.",
        exists=True,
    ),
    model: str = typer.Option(
        "gpt-4o",
        "--model",
        "-m",
        help="OpenAI model for pricing (gpt-4o, gpt-4o-mini).",
    ),
    batch_size: int = typer.Option(
        50,
        "--batch-size",
        help="Symbols per batch (for batch count calculation).",
    ),
    exclude: Optional[list[str]] = typer.Option(
        None,
        "--exclude",
        "-e",
        help="Glob patterns to exclude (e.g., '**/test/**').",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show detailed breakdown.",
    ),
):
    """Estimate cost and token budget before running analysis.

    Scans a Java project, extracts symbols, and calculates projected
    token usage and costs for both streaming and batch modes.
    No LLM calls are made.

    Examples:
        named estimate ./my-project
        named estimate ./project --model gpt-4o-mini
        named estimate ./project --batch-size 100 --verbose
    """
    import math

    console.print("\n[bold blue]Named[/bold blue] - Cost Estimation\n")

    # --- Find Java files (same as analyze) ---
    if path.is_file():
        if not path.suffix == ".java":
            console.print(f"[red]Error:[/red] Not a Java file: {path}")
            raise typer.Exit(1)
        java_files = [path]
    else:
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

    # --- Extract symbols (same as analyze) ---
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

    console.print(f"\nExtracted [bold]{len(all_symbols)}[/bold] symbols")

    if parse_errors:
        console.print(f"[yellow]Warning:[/yellow] {len(parse_errors)} file(s) had parse errors")
        if verbose:
            for error in parse_errors[:5]:
                console.print(f"  - {error}")
            if len(parse_errors) > 5:
                console.print(f"  ... and {len(parse_errors) - 5} more")

    _show_symbol_summary(all_symbols)

    # --- Pre-filter symbols ---
    from named.validation.validator import pre_filter_symbols

    analyzable, blocked = pre_filter_symbols(all_symbols)

    if not analyzable:
        console.print("\n[yellow]No analyzable symbols after guardrail filtering.[/yellow]")
        raise typer.Exit(0)

    # --- Build prompts and estimate tokens ---
    from named.prompts import get_system_prompt, get_rules_context
    from named.rules.guardrails import GUARDRAILS
    from named.rules.naming_rules import NAMING_RULES

    system_prompt = get_system_prompt()
    rules_context = get_rules_context(NAMING_RULES, GUARDRAILS)

    total_input_chars = 0
    for symbol in analyzable:
        # Inline prompt building (same logic as batch_client._build_symbol_prompt)
        symbol_info = f"Symbol to analyze:\nName: {symbol.name}\nKind: {symbol.kind}\nContext:\n```\n{symbol.context or ''}\n```\n"
        if symbol.annotations:
            symbol_info += f"\nAnnotations: {', '.join(symbol.annotations)}"
        user_prompt = f"{rules_context}\n\n{symbol_info}\n\nAnalyze this symbol and provide a JSON response following the schema."
        total_input_chars += len(system_prompt) + len(user_prompt)

    # Token estimation (chars / 4, validated against production data)
    total_input_tokens = total_input_chars // 4
    output_tokens_per_symbol = 500
    total_output_tokens = len(analyzable) * output_tokens_per_symbol
    avg_input_tokens = total_input_tokens // len(analyzable)

    # Batch count
    num_batches = math.ceil(len(analyzable) / batch_size)

    # --- Calculate costs ---
    if model not in MODEL_PRICING:
        console.print(f"[yellow]Warning:[/yellow] Unknown model '{model}', using gpt-4o pricing")
        pricing = MODEL_PRICING["gpt-4o"]
    else:
        pricing = MODEL_PRICING[model]

    streaming_input_cost = (total_input_tokens / 1_000_000) * pricing["streaming"]["input"]
    streaming_output_cost = (total_output_tokens / 1_000_000) * pricing["streaming"]["output"]
    streaming_total = streaming_input_cost + streaming_output_cost

    batch_input_cost = (total_input_tokens / 1_000_000) * pricing["batch"]["input"]
    batch_output_cost = (total_output_tokens / 1_000_000) * pricing["batch"]["output"]
    batch_total = batch_input_cost + batch_output_cost

    # --- Display token estimation table ---
    token_table = Table(title="Token Estimation")
    token_table.add_column("Metric", style="cyan")
    token_table.add_column("Value", justify="right")

    token_table.add_row("Analyzable symbols", f"{len(analyzable):,}")
    token_table.add_row("Blocked by guardrails", f"{len(blocked):,}")
    token_table.add_row("Avg input tokens/symbol", f"{avg_input_tokens:,}")
    token_table.add_row("Est. output tokens/symbol", f"{output_tokens_per_symbol:,}")
    token_table.add_row("Total input tokens", f"{total_input_tokens:,}")
    token_table.add_row("Total output tokens", f"{total_output_tokens:,}")
    token_table.add_row("Total tokens", f"{total_input_tokens + total_output_tokens:,}")
    token_table.add_row(f"Batches needed (size={batch_size})", f"{num_batches:,}")

    console.print()
    console.print(token_table)

    # --- Display cost comparison table ---
    cost_table = Table(title=f"Cost Estimate ({model})")
    cost_table.add_column("", style="bold")
    cost_table.add_column("Streaming", justify="right", style="yellow")
    cost_table.add_column("Batch (50% off)", justify="right", style="green")

    cost_table.add_row(
        "Input cost",
        f"${streaming_input_cost:.2f}",
        f"${batch_input_cost:.2f}",
    )
    cost_table.add_row(
        "Output cost",
        f"${streaming_output_cost:.2f}",
        f"${batch_output_cost:.2f}",
    )
    cost_table.add_row(
        "Total",
        f"${streaming_total:.2f}",
        f"${batch_total:.2f}",
    )
    cost_table.add_row(
        "Savings",
        "-",
        f"${streaming_total - batch_total:.2f}",
    )

    console.print()
    console.print(cost_table)

    # --- Summary ---
    console.print(f"\n[bold]Recommendation:[/bold]")
    if len(analyzable) > 500:
        console.print(
            f"  Use [green]batch mode[/green] for this project "
            f"(saves ${streaming_total - batch_total:.2f}, "
            f"{num_batches} batches, ~24h processing)"
        )
    else:
        console.print(
            f"  Use [yellow]streaming mode[/yellow] for quick results "
            f"(${streaming_total:.2f}, immediate processing)"
        )
    console.print()


@app.command()
def batch_status(
    batch_jobs: Path = typer.Option(
        ...,
        "--batch-jobs",
        help="Path to batch_jobs.json file",
        exists=True,
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show detailed output",
    ),
):
    """Check status of batch analysis jobs.

    This command checks the current status of previously submitted batch jobs.
    It queries the OpenAI API to get the latest status of each batch.

    Examples:
        named batch-status --batch-jobs ./report/batch_jobs.json
        named batch-status --batch-jobs ./report/batch_jobs.json --verbose
    """
    import json

    from named.config import get_settings
    from named.suggestions.batch_client import BatchAnalysisClient

    settings = get_settings()

    if not settings.openai_api_key:
        console.print("[red]Error:[/red] NAMED_OPENAI_API_KEY environment variable not set")
        raise typer.Exit(1)

    console.print("\n[bold blue]Named[/bold blue] - Batch Status Check\n")

    # Load batch jobs
    try:
        with open(batch_jobs) as f:
            jobs_data = json.load(f)
    except Exception as e:
        console.print(f"[red]Error:[/red] Failed to load batch jobs file: {e}")
        raise typer.Exit(1)

    if not jobs_data:
        console.print("[yellow]No batch jobs found in file.[/yellow]")
        raise typer.Exit(0)

    batch_client = BatchAnalysisClient(api_key=settings.openai_api_key)

    # Check each batch
    console.print(f"Checking {len(jobs_data)} batch job(s)...\n")

    completed = []
    in_progress = []
    failed = []

    for job_data in jobs_data:
        batch_id = job_data["batch_id"]

        try:
            # Retrieve current status
            status = batch_client.get_batch_status(batch_id)

            if status == "completed":
                completed.append(batch_id)
                console.print(f"[green]✓[/green] {batch_id}: Completed")
            elif status in ["validating", "in_progress"]:
                in_progress.append(batch_id)
                status_display = status.replace("_", " ").title()
                console.print(f"[yellow]⏱[/yellow] {batch_id}: {status_display}")
            else:
                failed.append(batch_id)
                console.print(f"[red]✗[/red] {batch_id}: {status.title()}")

            if verbose:
                console.print(f"    Created at: {job_data.get('created_at', 'unknown')}")
                console.print(f"    Symbols: {len(job_data.get('symbols', []))}")

        except Exception as e:
            console.print(f"[red]✗[/red] {batch_id}: Error - {e}")
            failed.append(batch_id)

    # Summary
    console.print(f"\n[bold]Summary:[/bold]")
    console.print(f"  Completed: {len(completed)}")
    console.print(f"  In Progress: {len(in_progress)}")
    console.print(f"  Failed: {len(failed)}")

    if completed == jobs_data:
        console.print("\n[green]✓ All batches completed![/green]")
        console.print(f"\nTo retrieve results, run:")
        console.print(f"  [cyan]named batch-retrieve --batch-jobs {batch_jobs}[/cyan]\n")
    elif in_progress:
        console.print("\n[yellow]⏱ Some batches still processing. Check again later.[/yellow]\n")
    elif failed:
        console.print("\n[red]✗ Some batches failed. Check the errors above.[/red]\n")


@app.command()
def batch_retrieve(
    batch_jobs: Path = typer.Option(
        ...,
        "--batch-jobs",
        help="Path to batch_jobs.json file",
        exists=True,
    ),
    output: Path = typer.Option(
        Path("./named-report"),
        "--output",
        "-o",
        help="Output directory for analysis results",
    ),
    format: str = typer.Option(
        "all",
        "--format",
        "-f",
        help="Output format: json, md, or all",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show detailed output",
    ),
):
    """Retrieve and process completed batch analysis results.

    This command downloads results from completed batch jobs, processes them,
    and generates the final analysis reports.

    Examples:
        named batch-retrieve --batch-jobs ./report/batch_jobs.json
        named batch-retrieve --batch-jobs ./report/batch_jobs.json --output ./final-report
    """
    import json

    from named.config import get_settings
    from named.suggestions.batch_client import BatchAnalysisClient, BatchJob

    settings = get_settings()

    if not settings.openai_api_key:
        console.print("[red]Error:[/red] NAMED_OPENAI_API_KEY environment variable not set")
        raise typer.Exit(1)

    # Validate format
    if format not in ("json", "md", "all"):
        console.print(f"[red]Error:[/red] Invalid format '{format}'. Use: json, md, or all")
        raise typer.Exit(1)

    console.print("\n[bold blue]Named[/bold blue] - Retrieve Batch Results\n")

    # Load batch jobs
    try:
        with open(batch_jobs) as f:
            jobs_data = json.load(f)
    except Exception as e:
        console.print(f"[red]Error:[/red] Failed to load batch jobs file: {e}")
        raise typer.Exit(1)

    if not jobs_data:
        console.print("[yellow]No batch jobs found in file.[/yellow]")
        raise typer.Exit(0)

    batch_client = BatchAnalysisClient(api_key=settings.openai_api_key)

    # Retrieve all completed batches
    all_results = []
    all_symbols = []
    skipped_count = 0

    for job_data in jobs_data:
        job = BatchJob(**job_data)

        # Check if completed
        try:
            status = batch_client.get_batch_status(job.batch_id)

            if status != "completed":
                console.print(
                    f"[yellow]⚠[/yellow] Batch {job.batch_id} not completed yet ({status})"
                )
                skipped_count += 1
                continue

            # Download results
            console.print(f"[cyan]↓[/cyan] Downloading results from {job.batch_id}...")
            batch_response = batch_client.client.batches.retrieve(job.batch_id)
            job.output_file_id = batch_response.output_file_id

            results = batch_client.download_results(job)

            # Parse results
            parsed = batch_client.parse_batch_results(results, job)

            console.print(f"  Parsed {len(parsed)} results")

            # Convert to NameSuggestion objects and validate
            from named.suggestions.llm_client import parse_llm_response
            from named.validation.validator import validate_suggestion
            from named.analysis.reference_finder import find_references
            from named.analysis.impact_analyzer import compute_rename_impact

            # We need java_files for reference finding
            # Extract from symbol file paths
            java_files = list(set(Path(s["file"]) for s in job.symbols))

            for symbol_idx, suggestion_data in parsed.items():
                if symbol_idx >= len(job.symbols):
                    console.print(
                        f"[yellow]Warning:[/yellow] Symbol index {symbol_idx} out of range"
                    )
                    continue

                symbol = job.symbols[symbol_idx]

                # Parse into NameSuggestion
                try:
                    suggestion = parse_llm_response(suggestion_data, symbol["name"])

                    if suggestion:
                        # Find references
                        refs = find_references(
                            symbol_name=symbol["name"],
                            symbol_kind=symbol["kind"],
                            java_files=java_files,
                            parent_class=symbol.get("parent_class"),
                        )
                        suggestion.references = refs
                        suggestion.location = {
                            "file": symbol["file"],
                            "line": symbol["line"],
                        }

                        # Compute impact
                        suggestion.impact_analysis = compute_rename_impact(refs)

                        # Validate
                        result = validate_suggestion(suggestion, symbol.get("annotations", []))
                        all_results.append(result)

                        if verbose and suggestion.suggested_name:
                            ref_count = len(refs)
                            console.print(
                                f"  [green]→[/green] {symbol['name']} → {suggestion.suggested_name} "
                                f"({suggestion.confidence:.0%}) [dim]({ref_count} refs)[/dim]"
                            )

                except Exception as e:
                    console.print(
                        f"[yellow]Warning:[/yellow] Failed to parse result for symbol {symbol['name']}: {e}"
                    )

            console.print(f"  [green]✓[/green] Retrieved {len(parsed)} results from batch {job.batch_id}\n")

        except Exception as e:
            console.print(f"[red]✗[/red] Failed to retrieve batch {job.batch_id}: {e}\n")
            continue

    if not all_results:
        console.print("\n[yellow]No results to export.[/yellow]")
        if skipped_count > 0:
            console.print(f"\n{skipped_count} batch(es) not yet completed. Run batch-status to check.")
        raise typer.Exit(0)

    # Reconstruct all_symbols from batch jobs
    for job_data in jobs_data:
        all_symbols.extend(job_data.get("symbols", []))

    # Get project path from first symbol
    project_path = Path(all_symbols[0]["file"]).parent if all_symbols else Path(".")

    # Export results
    console.print(f"[bold]Generating reports...[/bold]")

    output.mkdir(parents=True, exist_ok=True)

    if format in ("json", "all"):
        from named.export.json_exporter import export_json_string
        import json

        # Need to convert symbol dicts back to Symbol objects for export
        # For now, we'll use a simplified version
        json_content = _export_batch_json(all_results, all_symbols, project_path)

        json_path = output / "report.json"
        with open(json_path, "w", encoding="utf-8") as f:
            f.write(json_content)

        console.print(f"  - JSON: {json_path}")

    if format in ("md", "all"):
        from named.export.markdown_exporter import _build_markdown_report
        from datetime import datetime

        # Build markdown report
        md_content = _build_markdown_report_from_batch(all_results, all_symbols, project_path)

        md_path = output / "report.md"
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md_content)

        console.print(f"  - Markdown: {md_path}")

    # Show results summary
    _show_results_summary(all_results)

    console.print("\n[bold green]Batch analysis complete![/bold green]")
    console.print(f"Reports saved to: {output.absolute()}\n")


def _export_batch_json(results: list, symbols: list, project_path: Path) -> str:
    """Export batch results to JSON format."""
    import json
    from datetime import datetime

    # Build summary
    total_symbols = len(symbols)
    suggestions_count = sum(1 for r in results if r.suggestion.suggested_name)
    valid_suggestions = sum(1 for r in results if r.is_valid and r.suggestion.suggested_name)
    blocked_count = sum(1 for r in results if r.suggestion.blocked)

    confidences = [r.suggestion.confidence for r in results if r.suggestion.suggested_name]
    avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

    summary = {
        "total_symbols_analyzed": total_symbols,
        "suggestions_generated": suggestions_count,
        "valid_suggestions": valid_suggestions,
        "blocked_suggestions": blocked_count,
        "average_confidence": round(avg_confidence, 2),
    }

    report = {
        "metadata": {
            "project_path": str(project_path.absolute()),
            "generated_at": datetime.now().isoformat(),
            "llm_model": "gpt-4o",
            "named_version": "0.4.0",
            "processing_mode": "batch",
        },
        "summary": summary,
        "suggestions": [r.to_dict() for r in results if r.suggestion.suggested_name],
    }

    return json.dumps(report, indent=2, ensure_ascii=False)


def _build_markdown_report_from_batch(results: list, symbols: list, project_path: Path) -> str:
    """Build markdown report from batch results."""
    from datetime import datetime

    lines = ["# Named Analysis Report\n"]
    lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    lines.append(f"**Project:** {project_path.absolute()}\n")
    lines.append(f"**Model:** gpt-4o (batch mode)\n")
    lines.append("\n## Summary\n")

    total_symbols = len(symbols)
    suggestions_count = sum(1 for r in results if r.suggestion.suggested_name)
    valid_suggestions = sum(1 for r in results if r.is_valid and r.suggestion.suggested_name)

    lines.append(f"- Total symbols analyzed: {total_symbols}\n")
    lines.append(f"- Suggestions generated: {suggestions_count}\n")
    lines.append(f"- Valid suggestions: {valid_suggestions}\n")

    lines.append("\n## Suggestions\n")

    for result in sorted(
        [r for r in results if r.is_valid and r.suggestion.suggested_name],
        key=lambda r: -r.suggestion.confidence,
    ):
        s = result.suggestion
        lines.append(f"\n### {s.original_name} → {s.suggested_name}\n")
        lines.append(f"**Confidence:** {s.confidence:.0%}\n")
        lines.append(f"**Kind:** {s.symbol_kind}\n")
        lines.append(f"**Reasoning:** {s.reasoning}\n")

    return "".join(lines)


def _symbol_to_dict(symbol) -> dict:
    """Convert Symbol to dict for batch processing."""
    return {
        "name": symbol.name,
        "kind": symbol.kind,
        "annotations": symbol.annotations,
        "context": symbol.context,
        "file": str(symbol.location.file),
        "line": symbol.location.line,
        "parent_class": symbol.parent_class,
    }


def _save_batch_jobs(batch_jobs: list, output_path: Path) -> Path:
    """Save batch job information to JSON file."""
    import json

    jobs_data = [job.to_dict() for job in batch_jobs]

    jobs_file = output_path / "batch_jobs.json"
    with open(jobs_file, "w", encoding="utf-8") as f:
        json.dump(jobs_data, f, indent=2, ensure_ascii=False)

    return jobs_file


def _handle_batch_mode(
    analyzable: list,
    all_symbols: list,
    java_files: list,
    output: Path,
    project_path: Path,
    model: str,
):
    """Handle batch processing mode."""
    from named.config import get_settings
    from named.suggestions.batch_client import BatchAnalysisClient

    settings = get_settings()

    console.print("\n[yellow]⏱ Batch mode:[/yellow] Processing will take ~24 hours")
    console.print("[yellow]💰 Cost savings:[/yellow] 50% discount vs streaming\n")

    # Get API key
    if not settings.openai_api_key:
        console.print("[red]Error:[/red] NAMED_OPENAI_API_KEY environment variable not set")
        raise typer.Exit(1)

    # Initialize batch client
    batch_client = BatchAnalysisClient(api_key=settings.openai_api_key, model=model)

    # Group symbols into batches
    batch_size = settings.batch_size
    symbol_batches = [
        analyzable[i : i + batch_size] for i in range(0, len(analyzable), batch_size)
    ]

    console.print(
        f"Submitting {len(symbol_batches)} batch(es) of up to {batch_size} symbols each...\n"
    )

    # Get system prompt and rules context
    from named.prompts import get_system_prompt, get_rules_context
    from named.rules.naming_rules import NAMING_RULES
    from named.rules.guardrails import GUARDRAILS

    system_prompt = get_system_prompt()
    rules_context = get_rules_context(NAMING_RULES, GUARDRAILS)

    # Submit all batches
    batch_jobs = []
    for i, batch_symbols in enumerate(symbol_batches):
        # Convert symbols to dicts
        symbol_dicts = [_symbol_to_dict(s) for s in batch_symbols]

        # Generate batch requests
        requests = batch_client.create_batch_requests(
            symbols=symbol_dicts, system_prompt=system_prompt, rules_context=rules_context
        )

        # Submit batch
        try:
            job = batch_client.submit_batch(
                requests=requests,
                symbols=symbol_dicts,
                description=f"Named batch {i+1}/{len(symbol_batches)}",
            )
            batch_jobs.append(job)

            console.print(
                f"  [green]✓[/green] Batch {i+1} submitted (batch_id={job.batch_id})"
            )
        except Exception as e:
            console.print(f"  [red]✗[/red] Failed to submit batch {i+1}: {e}")
            raise typer.Exit(1)

    # Save batch job info
    output.mkdir(parents=True, exist_ok=True)
    jobs_file = _save_batch_jobs(batch_jobs, output)

    console.print(f"\n[green]✓[/green] All batches submitted!")
    console.print(f"\nBatch jobs saved to: {jobs_file}")
    console.print(f"\nTo check status later, run:")
    console.print(f"  [cyan]named batch-status --batch-jobs {jobs_file}[/cyan]")
    console.print(f"\nTo retrieve results when completed (~24 hours), run:")
    console.print(f"  [cyan]named batch-retrieve --batch-jobs {jobs_file} --output {output}[/cyan]\n")


if __name__ == "__main__":
    app()
