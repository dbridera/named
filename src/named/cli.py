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
def config():
    """Show current configuration (env + effective values). No secrets printed."""
    from named.config import get_settings

    settings = get_settings()
    console.print("\n[bold]Named configuration[/bold]\n")
    # Auth
    has_key = bool(settings.openai_api_key)
    has_azure = bool(settings.azure_openai_endpoint and settings.azure_openai_deployment_name)
    console.print("[bold]Auth:[/bold]")
    console.print(f"  OpenAI API key: {'(set)' if has_key else '(not set)'}")
    console.print(f"  Azure: {'(endpoint + deployment set)' if has_azure else '(not set)'}\n")
    # URLs / models
    console.print("[bold]OpenAI / Azure:[/bold]")
    console.print(f"  openai_base_url: {settings.openai_base_url or '(not set)'}")
    console.print(f"  openai_model: {settings.openai_model}")
    if settings.azure_openai_endpoint:
        console.print(f"  AZURE_OPENAI_ENDPOINT: {settings.azure_openai_endpoint}")
    console.print(f"  AZURE_OPENAI_DEPLOYMENT_NAME: {settings.azure_openai_deployment_name or '(not set)'}")
    console.print(f"  AZURE_OPENAI_BATCH_DEPLOYMENT_NAME: {settings.azure_openai_batch_deployment_name or '(not set)'}")
    console.print(f"  AZURE_OPENAI_API_VERSION: {settings.azure_openai_api_version}")
    console.print(f"  AZURE_CLIENT_ID: {settings.azure_client_id or '(not set)'}\n")
    # Effective
    console.print("[bold]Effective (used at runtime):[/bold]")
    console.print(f"  effective_openai_model (streaming): {settings.effective_openai_model()}")
    console.print(f"  effective_batch_model (batch): {settings.effective_batch_model()}\n")
    # Batch
    console.print("[bold]Batch:[/bold]")
    console.print(f"  batch_size: {settings.batch_size}")
    console.print(f"  batch_poll_interval: {settings.batch_poll_interval}s")
    console.print()


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

    # Analyze with LLM (per-file batching: one call per file)
    results = []

    try:
        from rich.progress import BarColumn, TaskProgressColumn, TimeRemainingColumn

        from named.prompts import get_rules_context
        from named.rules.guardrails import GUARDRAILS
        from named.rules.naming_rules import NAMING_RULES
        from named.suggestions.llm_client import LLMClient, LLMError

        client = LLMClient(model=model, verbose=verbose)

        # Pre-render rules context once — reused for every file
        rules_context = get_rules_context(NAMING_RULES, GUARDRAILS, include_schema=False)

        # Group symbols by file
        symbols_by_file: dict[Path, list] = {}
        for symbol in analyzable:
            file_path = symbol.location.file
            if file_path not in symbols_by_file:
                symbols_by_file[file_path] = []
            symbols_by_file[file_path].append(symbol)

        total_files = len(symbols_by_file)

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
                total=total_files,
            )

            for file_idx, (file_path, file_symbols) in enumerate(symbols_by_file.items()):
                file_name = file_path.name
                progress.update(
                    task,
                    description=f"[cyan]{file_name}[/cyan] ({len(file_symbols)} symbols)",
                )

                if verbose:
                    console.print(
                        f"\n[dim]File {file_idx + 1}/{total_files}: {file_name} "
                        f"({len(file_symbols)} symbols)[/dim]"
                    )

                # One API call for the entire file
                suggestions = client.analyze_file(
                    file_path=file_path,
                    symbols=file_symbols,
                    rules_context=rules_context,
                )

                # Process returned suggestions (parallel list to file_symbols)
                from named.suggestions.common import enrich_suggestion

                for symbol, suggestion in zip(file_symbols, suggestions):
                    if suggestion is None:
                        continue

                    result = enrich_suggestion(
                        suggestion=suggestion,
                        symbol_name=symbol.name,
                        symbol_kind=symbol.kind,
                        symbol_file=str(symbol.location.file),
                        symbol_line=symbol.location.line,
                        parent_class=symbol.parent_class,
                        annotations=symbol.annotations,
                        java_files=java_files,
                    )

                    if result:
                        results.append(result)
                        if verbose:
                            s = result.suggestion
                            console.print(
                                f"  [green]→[/green] {s.original_name} → {s.suggested_name} "
                                f"({s.confidence:.0%}) [dim]({len(s.references)} refs)[/dim]"
                            )

                progress.advance(task)

    except LLMError as e:
        console.print(f"\n[red]Error:[/red] LLM client error: {e}")
        console.print("\nMake sure NAMED_OPENAI_API_KEY environment variable is set.")
        raise typer.Exit(1)

    # Post-validation and export (shared with batch mode)
    from named.suggestions.common import export_reports, post_validate_results

    results, conflicts_found = post_validate_results(results, all_symbols)
    if conflicts_found > 0:
        console.print(
            f"\n[yellow]Warning:[/yellow] Blocked {conflicts_found} suggestion(s) "
            f"due to naming conflicts (duplicate targets, overrides, or shadow collisions)"
        )

    console.print("\n[bold]Generating reports...[/bold]")
    paths = export_reports(results, all_symbols, output, project_path, model, format)
    for fmt, path in paths.items():
        console.print(f"  - {fmt.upper()}: {path}")

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
        run_metadata, jobs_data = _load_batch_jobs(batch_jobs)
    except Exception as e:
        console.print(f"[red]Error:[/red] Failed to load batch jobs file: {e}")
        raise typer.Exit(1)

    if not jobs_data:
        console.print("[yellow]No batch jobs found in file.[/yellow]")
        raise typer.Exit(0)

    # Show run info if available
    if run_metadata.get("run_id"):
        console.print(f"[dim]Run ID: {run_metadata['run_id']}[/dim]")
        if run_metadata.get("project_path"):
            console.print(f"[dim]Project: {run_metadata['project_path']}[/dim]")
        if run_metadata.get("created_at"):
            console.print(f"[dim]Created: {run_metadata['created_at']}[/dim]")
        console.print()

    batch_client = BatchAnalysisClient(
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url or None,
    )

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
            elif status in ["validating", "in_progress", "finalizing"]:
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
    model: str = typer.Option(
        "gpt-4o",
        "--model",
        "-m",
        help="Model used for analysis (for report metadata)",
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
        run_metadata, jobs_data = _load_batch_jobs(batch_jobs)
    except Exception as e:
        console.print(f"[red]Error:[/red] Failed to load batch jobs file: {e}")
        raise typer.Exit(1)

    if not jobs_data:
        console.print("[yellow]No batch jobs found in file.[/yellow]")
        raise typer.Exit(0)

    # Use model from run metadata if available (CLI flag overrides)
    if model == "gpt-4o" and run_metadata.get("model"):
        model = run_metadata["model"]

    # Show run info if available
    if run_metadata.get("run_id"):
        console.print(f"[dim]Run ID: {run_metadata['run_id']}[/dim]")
        if run_metadata.get("project_path"):
            console.print(f"[dim]Project: {run_metadata['project_path']}[/dim]")
        console.print()

    batch_client = BatchAnalysisClient(
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url or None,
    )

    # Collect all java files across all batch jobs for reference finding
    all_java_files = list(set(
        Path(s["file"])
        for job_data in jobs_data
        for s in job_data.get("symbols", [])
    ))

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
            from named.suggestions.common import enrich_suggestion
            from named.rules.models import NameSuggestion

            is_file_format = job.file_map is not None

            for symbol_idx, suggestion_data in parsed.items():
                if symbol_idx >= len(job.symbols):
                    console.print(
                        f"[yellow]Warning:[/yellow] Symbol index {symbol_idx} out of range"
                    )
                    continue

                symbol = job.symbols[symbol_idx]

                try:
                    # Per-file format: suggestion_data has {symbol_index, needs_rename, suggestion: {...}}
                    # Legacy format: suggestion_data is the raw LLM JSON
                    if is_file_format:
                        s = suggestion_data.get("suggestion", {})
                        if not s:
                            continue
                        suggestion = NameSuggestion(
                            original_name=symbol["name"],
                            suggested_name=s.get("suggested_name", ""),
                            symbol_kind=symbol["kind"],
                            confidence=s.get("confidence", 0.0),
                            rationale=s.get("rationale", ""),
                            rules_addressed=s.get("rules_addressed", []),
                        )
                    else:
                        suggestion = parse_llm_response(suggestion_data, symbol["name"])

                    if suggestion:
                        result = enrich_suggestion(
                            suggestion=suggestion,
                            symbol_name=symbol["name"],
                            symbol_kind=symbol["kind"],
                            symbol_file=symbol["file"],
                            symbol_line=symbol["line"],
                            parent_class=symbol.get("parent_class"),
                            annotations=symbol.get("annotations", []),
                            java_files=all_java_files,
                        )

                        if result:
                            all_results.append(result)
                            if verbose:
                                s = result.suggestion
                                console.print(
                                    f"  [green]→[/green] {s.original_name} → {s.suggested_name} "
                                    f"({s.confidence:.0%}) [dim]({len(s.references)} refs)[/dim]"
                                )
                        elif verbose:
                            console.print(
                                f"  [yellow]Filtered:[/yellow] {symbol['name']} → "
                                f"{suggestion.suggested_name} (hallucinated method-style name)"
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

    # Reconstruct all_symbols as Symbol objects.
    # Prefer the full all_symbols list from run metadata (includes blocked symbols),
    # falling back to job-level symbols for backward compatibility.
    from named.suggestions.common import export_reports, post_validate_results, reconstruct_symbol

    if run_metadata.get("all_symbols"):
        all_symbol_dicts = run_metadata["all_symbols"]
    else:
        all_symbol_dicts = []
        for job_data in jobs_data:
            all_symbol_dicts.extend(job_data.get("symbols", []))

    all_symbols = [reconstruct_symbol(sd) for sd in all_symbol_dicts]

    # Post-validation and export (shared with streaming mode)
    all_results, conflicts_found = post_validate_results(all_results, all_symbols)
    if conflicts_found > 0:
        console.print(
            f"\n[yellow]Warning:[/yellow] Blocked {conflicts_found} suggestion(s) "
            f"due to naming conflicts (duplicate targets, overrides, or shadow collisions)"
        )

    project_path = Path(run_metadata.get("project_path", all_symbol_dicts[0]["file"])) if all_symbol_dicts else Path(".")

    console.print(f"\n[bold]Generating reports...[/bold]")
    paths = export_reports(all_results, all_symbols, output, project_path, model, format)
    for fmt, path in paths.items():
        console.print(f"  - {fmt.upper()}: {path}")

    _show_results_summary(all_results)

    console.print("\n[bold green]Batch analysis complete![/bold green]")
    console.print(f"Reports saved to: {output.absolute()}\n")


@app.command()
def batch_cancel(
    batch_jobs: Optional[Path] = typer.Option(
        None,
        "--batch-jobs",
        help="Path to batch_jobs.json (from a previous analyze --mode batch run).",
        exists=True,
    ),
    ids_file: Optional[Path] = typer.Option(
        None,
        "--ids-file",
        help="Plain text file with one batch_id per line.",
        exists=True,
    ),
    delete_files: bool = typer.Option(
        True,
        "--delete-files/--no-delete-files",
        help="Also delete input files to free the 500-file quota.",
    ),
):
    """Cancel batch jobs and optionally delete their input files.

    Use when a batch run didn't finish and you want to free quota and start over.

    Examples:
        named batch-cancel --batch-jobs ./named-report/batch_jobs.json
        named batch-cancel --ids-file batch_ids.txt --no-delete-files
    """
    from named.config import get_settings
    from named.suggestions.batch_client import BatchAnalysisClient

    if not batch_jobs and not ids_file:
        console.print("[red]Error:[/red] Provide either --batch-jobs or --ids-file.")
        raise typer.Exit(1)
    if batch_jobs and ids_file:
        console.print("[red]Error:[/red] Provide only one of --batch-jobs or --ids-file.")
        raise typer.Exit(1)

    settings = get_settings()
    if not settings.openai_api_key and not settings.azure_openai_endpoint:
        console.print(
            "[red]Error:[/red] Set NAMED_OPENAI_API_KEY or Azure Workload Identity "
            "(AZURE_OPENAI_ENDPOINT + AZURE_OPENAI_DEPLOYMENT_NAME)."
        )
        raise typer.Exit(1)

    # Collect (batch_id, input_file_id or None)
    entries: list[tuple[str, str | None]] = []
    if batch_jobs:
        _, jobs_list = _load_batch_jobs(batch_jobs)
        for job in jobs_list:
            bid = job.get("batch_id")
            fid = job.get("input_file_id")
            if bid:
                entries.append((bid, fid))
    else:
        with open(ids_file, encoding="utf-8") as f:
            for line in f:
                bid = line.strip()
                if bid and not bid.startswith("#"):
                    entries.append((bid, None))

    if not entries:
        console.print("[yellow]No batch IDs to cancel.[/yellow]")
        raise typer.Exit(0)

    batch_client = BatchAnalysisClient(
        api_key=settings.openai_api_key,
        model=settings.effective_batch_model(),
        base_url=settings.openai_base_url or None,
    )
    console.print(f"Cancelling {len(entries)} batch job(s)...\n")

    cancelled = 0
    deleted = 0
    errors = 0
    for batch_id, input_file_id in entries:
        try:
            if input_file_id is None:
                batch = batch_client.get_batch(batch_id)
                input_file_id = getattr(batch, "input_file_id", None)
            batch_client.cancel_batch(batch_id)
            cancelled += 1
            console.print(f"  [green]Cancelled[/green] {batch_id}")
            if delete_files and input_file_id:
                batch_client.delete_file(input_file_id)
                deleted += 1
                console.print(f"    Deleted file {input_file_id}")
        except Exception as e:
            errors += 1
            console.print(f"  [red]Failed[/red] {batch_id}: {e}")

    console.print(
        f"\n[bold]Done:[/bold] {cancelled} cancelled, {deleted} file(s) deleted, {errors} error(s).\n"
    )


@app.command()
def files_cleanup(
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Only list files, do not delete.",
    ),
    purpose: str = typer.Option(
        "batch",
        "--purpose",
        help="File purpose to list/delete (default: batch). Use 'all' to skip filter.",
    ),
):
    """List and delete files from the API to free the 500-file quota.

    Examples:
        named files-cleanup --dry-run
        named files-cleanup
        named files-cleanup --purpose all
    """
    from named.config import get_settings
    from named.suggestions.batch_client import BatchAnalysisClient

    settings = get_settings()
    if not settings.openai_api_key and not settings.azure_openai_endpoint:
        console.print(
            "[red]Error:[/red] Set NAMED_OPENAI_API_KEY or Azure Workload Identity "
            "(AZURE_OPENAI_ENDPOINT + AZURE_OPENAI_DEPLOYMENT_NAME)."
        )
        raise typer.Exit(1)

    client = BatchAnalysisClient(
        api_key=settings.openai_api_key,
        model=settings.effective_batch_model(),
        base_url=settings.openai_base_url or None,
    )
    purpose_filter = None if purpose == "all" else purpose
    files = client.list_files(purpose=purpose_filter, limit=1000)
    console.print(f"Found {len(files)} file(s).\n")
    if not files:
        raise typer.Exit(0)
    if dry_run:
        for f in files:
            console.print(f"  [dim]{getattr(f, 'id', f)}[/dim] {getattr(f, 'filename', '')}")
        console.print("\n[yellow]Dry run: no files deleted.[/yellow]\n")
        raise typer.Exit(0)
    deleted_count = 0
    error_count = 0
    for f in files:
        fid = getattr(f, "id", None)
        if not fid:
            continue
        try:
            client.delete_file(fid)
            deleted_count += 1
            console.print(f"  [green]Deleted[/green] {fid}")
        except Exception as e:
            error_count += 1
            console.print(f"  [red]Failed[/red] {fid}: {e}")
    console.print(f"\n[bold]Done:[/bold] {deleted_count} deleted, {error_count} error(s).\n")


def _symbol_to_dict(symbol) -> dict:
    """Convert Symbol to dict for batch processing."""
    d = {
        "name": symbol.name,
        "kind": symbol.kind,
        "annotations": symbol.annotations,
        "context": symbol.context,
        "file": str(symbol.location.file),
        "line": symbol.location.line,
        "parent_class": symbol.parent_class,
    }
    # Preserve fields needed by post-validation (override/shadow checks)
    if symbol.modifiers:
        d["modifiers"] = symbol.modifiers
    if symbol.extends_type:
        d["extends_type"] = symbol.extends_type
    if symbol.implements_types:
        d["implements_types"] = symbol.implements_types
    if symbol.parameter_types:
        d["parameter_types"] = symbol.parameter_types
    if symbol.method_locals:
        # Convert sets to lists for JSON serialization
        d["method_locals"] = {k: list(v) for k, v in symbol.method_locals.items()}
    return d


def _save_batch_jobs(
    batch_jobs: list,
    output_path: Path,
    run_id: str,
    project_path: str,
    model: str,
    total_symbols: int,
    all_symbols_dicts: list[dict] | None = None,
) -> Path:
    """Save batch job information to JSON file."""
    import json
    from datetime import datetime

    run_data = {
        "run_id": run_id,
        "created_at": datetime.now().isoformat(),
        "project_path": project_path,
        "model": model,
        "total_symbols": total_symbols,
        "total_batches": len(batch_jobs),
        "jobs": [job.to_dict() for job in batch_jobs],
    }
    if all_symbols_dicts is not None:
        run_data["all_symbols"] = all_symbols_dicts

    jobs_file = output_path / "batch_jobs.json"
    with open(jobs_file, "w", encoding="utf-8") as f:
        json.dump(run_data, f, indent=2, ensure_ascii=False)

    return jobs_file


def _load_batch_jobs(file_path: Path) -> tuple[dict, list[dict]]:
    """Load batch jobs file, handling both old (list) and new (object) formats.

    Returns:
        Tuple of (run_metadata, jobs_list).
        run_metadata contains run_id, project_path, model, etc.
        jobs_list is the list of job dicts.
    """
    import json

    with open(file_path) as f:
        data = json.load(f)

    # New format: object with "jobs" key
    if isinstance(data, dict) and "jobs" in data:
        metadata = {k: v for k, v in data.items() if k != "jobs"}
        return metadata, data["jobs"]

    # Old format: flat list of jobs
    return {}, data


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

    # Warn about batch mode on custom endpoints
    if settings.openai_base_url:
        console.print(
            "[yellow]Warning:[/yellow] Batch API may not be available on custom endpoints "
            "(e.g., Azure AI Foundry). If batch submission fails, use streaming mode instead.\n"
        )

    # Initialize batch client
    batch_client = BatchAnalysisClient(
        api_key=settings.openai_api_key,
        model=model,
        base_url=settings.openai_base_url or None,
    )

    # Get system prompt and rules context (same as streaming mode)
    from named.prompts import get_system_prompt, get_rules_context
    from named.rules.naming_rules import NAMING_RULES
    from named.rules.guardrails import GUARDRAILS

    system_prompt = get_system_prompt()
    rules_context = get_rules_context(NAMING_RULES, GUARDRAILS, include_schema=False)

    # Group symbols by file (same as streaming mode)
    symbols_by_file: dict[Path, list] = {}
    for symbol in analyzable:
        file_path = symbol.location.file
        symbols_by_file.setdefault(file_path, []).append(symbol)

    # Build file groups with full source (same as streaming reads each file)
    file_groups = []
    flat_symbols = []
    for file_path, file_symbols in symbols_by_file.items():
        try:
            file_source = file_path.read_text(encoding="utf-8")
        except Exception as e:
            console.print(f"[yellow]Warning:[/yellow] Could not read {file_path}: {e}")
            continue
        symbol_dicts = [_symbol_to_dict(s) for s in file_symbols]
        file_groups.append({
            "file_path": str(file_path),
            "file_source": file_source,
            "symbols": symbol_dicts,
        })
        flat_symbols.extend(symbol_dicts)

    # Create file-based batch requests (one per file/chunk, like streaming)
    all_requests, full_file_map = batch_client.create_file_batch_requests(
        file_groups=file_groups,
        system_prompt=system_prompt,
        rules_context=rules_context,
    )

    # Split requests into batches targeting batch_size symbols each.
    # file_map indices must be remapped to be batch-local (starting from 0).
    batch_size = settings.batch_size
    batches = []  # list of (requests, symbols_slice, file_map_slice)
    current_requests = []
    current_file_map = {}
    current_symbols = []
    current_count = 0

    for request in all_requests:
        cid = request["custom_id"]
        global_start, count = full_file_map[cid]

        # If adding this request exceeds batch_size, flush current batch
        if current_count + count > batch_size and current_requests:
            batches.append((current_requests, current_symbols, current_file_map))
            current_requests = []
            current_file_map = {}
            current_symbols = []
            current_count = 0

        current_requests.append(request)
        # Remap to batch-local index
        current_file_map[cid] = [current_count, count]
        current_symbols.extend(flat_symbols[global_start : global_start + count])
        current_count += count

    if current_requests:
        batches.append((current_requests, current_symbols, current_file_map))

    console.print(
        f"Submitting {len(batches)} batch(es) "
        f"({len(all_requests)} file requests, {len(flat_symbols)} symbols)...\n"
    )

    # Generate run ID
    import uuid
    from datetime import datetime

    run_id = f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
    console.print(f"[dim]Run ID: {run_id}[/dim]\n")

    # Submit batches sequentially with retry on token limit
    import time

    batch_jobs = []
    max_retries = 20
    retry_wait = 30
    validation_wait = 5

    for i, (batch_requests, batch_symbols, batch_file_map) in enumerate(batches):
        for attempt in range(max_retries):
            try:
                job = batch_client.submit_batch(
                    requests=batch_requests,
                    symbols=batch_symbols,
                    description=f"Named {run_id} batch {i+1}/{len(batches)}",
                    file_map=batch_file_map,
                )
            except Exception as e:
                console.print(f"  [red]✗[/red] Failed to submit batch {i+1}: {e}")
                raise typer.Exit(1)

            # Wait briefly then check if the batch was accepted or rejected
            time.sleep(validation_wait)
            try:
                status = batch_client.get_batch_status(job.batch_id)
            except Exception:
                status = "unknown"

            if status == "failed":
                try:
                    batch_resp = batch_client.client.batches.retrieve(job.batch_id)
                    errors = batch_resp.errors
                    is_token_limit = errors and any(
                        "token_limit" in (e.code or "") or "enqueued" in (e.message or "")
                        for e in (errors.data or [])
                    )
                except Exception:
                    is_token_limit = False

                if is_token_limit:
                    console.print(
                        f"  [yellow]⏱[/yellow] Batch {i+1}: Queue full, "
                        f"waiting {retry_wait}s for space... "
                        f"(attempt {attempt+1}/{max_retries})"
                    )
                    time.sleep(retry_wait)
                    continue
                else:
                    console.print(f"  [red]✗[/red] Batch {i+1} failed: {errors}")
                    raise typer.Exit(1)
            else:
                batch_jobs.append(job)
                console.print(
                    f"  [green]✓[/green] Batch {i+1} submitted (batch_id={job.batch_id})"
                )
                break
        else:
            console.print(
                f"  [red]✗[/red] Batch {i+1}: Failed after {max_retries} retries. "
                f"Queue never cleared."
            )
            raise typer.Exit(1)

    # Save batch job info
    output.mkdir(parents=True, exist_ok=True)
    # Serialize all symbols (including blocked) for report parity with streaming
    all_symbols_dicts = [_symbol_to_dict(s) for s in all_symbols]

    jobs_file = _save_batch_jobs(
        batch_jobs,
        output,
        run_id=run_id,
        project_path=str(project_path),
        model=model,
        total_symbols=len(all_symbols),
        all_symbols_dicts=all_symbols_dicts,
    )

    console.print(f"\n[green]✓[/green] All batches submitted!")
    console.print(f"\nBatch jobs saved to: {jobs_file}")
    console.print(f"\nTo check status later, run:")
    console.print(f"  [cyan]named batch-status --batch-jobs {jobs_file}[/cyan]")
    console.print(f"\nTo retrieve results when completed (~24 hours), run:")
    console.print(f"  [cyan]named batch-retrieve --batch-jobs {jobs_file} --output {output}[/cyan]\n")


@app.command()
def apply(
    report: Path = typer.Argument(
        ...,
        help="Path to Named report JSON file.",
        exists=True,
    ),
    project_root: Optional[Path] = typer.Option(
        None,
        "--project-root",
        "-p",
        help="Root directory of the Java project (for resolving relative paths).",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Preview changes without modifying files.",
    ),
    min_confidence: float = typer.Option(
        0.80,
        "--min-confidence",
        "-c",
        help="Minimum confidence threshold (0.0-1.0).",
    ),
    backup: bool = typer.Option(
        True,
        "--backup/--no-backup",
        help="Create backup of files before modification.",
    ),
    verify: bool = typer.Option(
        False,
        "--verify",
        help="Run compilation check after applying renames.",
    ),
    output_dir: Optional[Path] = typer.Option(
        None,
        "--output-dir",
        "-o",
        help="Copy project here and apply renames to the copy (originals stay untouched).",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show detailed output for each rename.",
    ),
):
    """Apply naming suggestions from a report to Java source files.

    Reads a Named report JSON and renames symbols at their declaration
    and all reference locations.

    Examples:
        named apply ./named-report/report.json
        named apply ./report.json --dry-run
        named apply ./report.json --min-confidence 0.90 --project-root ./my-project
        named apply ./report.json --no-backup --verify
    """
    from named.apply.rename_engine import apply_renames, get_file_diff
    from named.apply.report_loader import extract_replacement_sites, load_report
    from named.apply.models import FileChange

    console.print("\n[bold blue]Named[/bold blue] - Apply Suggestions\n")

    # Load report
    try:
        report_data = load_report(report)
    except (ValueError, Exception) as e:
        console.print(f"[red]Error:[/red] Failed to load report: {e}")
        raise typer.Exit(1)

    metadata = report_data.get("metadata", {})
    suggestions = report_data.get("suggestions", [])
    console.print(f"Report: {report}")
    console.print(f"  Model: {metadata.get('llm_model', 'unknown')}")
    console.print(f"  Generated: {metadata.get('generated_at', 'unknown')}")
    console.print(f"  Total suggestions: {len(suggestions)}")

    # Extract replacement sites
    resolved_root = project_root or Path(metadata.get("project_path", "."))
    sites = extract_replacement_sites(
        report_data,
        project_root=resolved_root,
        min_confidence=min_confidence,
    )

    if not sites:
        console.print(
            f"\n[yellow]No applicable suggestions found "
            f"(confidence >= {min_confidence:.0%}).[/yellow]"
        )
        raise typer.Exit(0)

    # Group by file for summary
    from collections import defaultdict

    files_affected: dict[Path, int] = defaultdict(int)
    for site in sites:
        files_affected[site.file] += 1

    declarations = sum(1 for s in sites if s.site_type == "declaration")
    references = sum(1 for s in sites if s.site_type == "reference")

    console.print(f"\n[bold]Apply Plan:[/bold]")
    console.print(f"  Replacements: {len(sites)} ({declarations} declarations, {references} references)")
    console.print(f"  Files affected: {len(files_affected)}")
    console.print(f"  Confidence threshold: {min_confidence:.0%}")

    if verbose:
        console.print(f"\n  Files:")
        for file_path, count in sorted(files_affected.items()):
            console.print(f"    {file_path.name}: {count} replacements")

    # Dry run mode - show preview
    if dry_run:
        console.print("\n[yellow]Dry run mode:[/yellow] Previewing changes...\n")
        result = apply_renames(sites, dry_run=True, backup=False)

        # Show diffs
        from collections import defaultdict as dd

        sites_by_file = dd(list)
        for site in sites:
            sites_by_file[site.file].append(site)

        for file_path, file_sites in sites_by_file.items():
            if not file_path.exists():
                console.print(f"[red]  File not found: {file_path}[/red]")
                continue

            content = file_path.read_text(encoding="utf-8")
            change = FileChange(file=file_path, original_content=content)

            # Simulate the changes
            from named.apply.rename_engine import _process_file

            temp_result = type(result)()
            processed = _process_file(file_path, file_sites, temp_result)

            if processed and processed.modified_content:
                diff = get_file_diff(processed)
                if diff:
                    console.print(f"[bold cyan]{file_path}[/bold cyan]")
                    for line in diff.split("\n"):
                        if line.startswith("- "):
                            console.print(f"  [red]{line}[/red]")
                        elif line.startswith("+ "):
                            console.print(f"  [green]{line}[/green]")
                        else:
                            console.print(f"  [dim]{line}[/dim]")
                    console.print()

        _show_apply_summary(result)
        console.print("\n[yellow]No files were modified (dry run).[/yellow]\n")
        raise typer.Exit(0)

    # If --output-dir, copy entire project there and remap paths
    if output_dir:
        import shutil

        output_dir = output_dir.resolve()
        abs_root = resolved_root.resolve()
        console.print(f"\n[bold]Copying project to {output_dir}...[/bold]")
        shutil.copytree(abs_root, output_dir, dirs_exist_ok=True)

        # Remap ReplacementSite file paths from original to copy
        for site in sites:
            rel = site.file.relative_to(abs_root)
            site.file = output_dir / rel

    # Apply renames
    console.print(f"\n[bold]Applying renames...[/bold]")

    result = apply_renames(
        sites,
        dry_run=False,
        backup=backup if not output_dir else False,
        backup_base=resolved_root / ".named-backup" if backup and not output_dir else None,
    )

    # Show results
    _show_apply_summary(result)

    if output_dir:
        console.print(f"\n  Applied to: {output_dir}")
    elif result.backup_dir:
        console.print(f"\n  Backups saved to: {result.backup_dir}")

    # Verification
    if verify and result.files_modified:
        console.print("\n[bold]Running compilation check...[/bold]")
        from named.apply.verifier import verify_compilation

        # Determine project root for compilation
        compile_root = project_root or Path(metadata.get("project_path", "."))
        success, message = verify_compilation(compile_root)

        if success:
            console.print(f"  [green]{message}[/green]")
        else:
            console.print(f"  [red]{message}[/red]")

    console.print("\n[bold green]Apply complete![/bold green]\n")


def _show_apply_summary(result):
    """Show summary of apply results."""
    from named.apply.models import ApplyResult

    console.print(f"\n[bold]Results:[/bold]")
    console.print(f"  Applied: [green]{len(result.applied)}[/green]")
    console.print(f"  Skipped: [yellow]{len(result.skipped)}[/yellow]")
    console.print(f"  Errors: [red]{len(result.errors)}[/red]")
    console.print(f"  Files modified: {len(result.files_modified)}")

    if result.skipped:
        console.print(f"\n  [yellow]Skipped details:[/yellow]")
        for site, reason in result.skipped[:10]:
            console.print(f"    {site.original_name} -> {site.new_name}: {reason}")
        if len(result.skipped) > 10:
            console.print(f"    ... and {len(result.skipped) - 10} more")

    if result.errors:
        console.print(f"\n  [red]Error details:[/red]")
        for site, reason in result.errors[:10]:
            console.print(f"    {site.original_name}: {reason}")
        if len(result.errors) > 10:
            console.print(f"    ... and {len(result.errors) - 10} more")


if __name__ == "__main__":
    app()
