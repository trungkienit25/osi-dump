import logging
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.logging import RichHandler
from rich.panel import Panel
from rich.tree import Tree
from rich import print as rprint

from osi_dump.services.orchestrator import DumpOrchestrator

# Initialize Typer App
app = typer.Typer(help="OSI Dump v2 - OpenStack Database Extraction Tool")
console = Console()

def setup_logging(verbose: bool = False):
    """Configures logging to use RichHandler for pretty console output."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(console=console, rich_tracebacks=True, show_path=False)]
    )

@app.command()
def main(
    config: Path = typer.Option(..., "--config", "-c", help="Path to config.json", exists=True, dir_okay=False),
    auth: Path = typer.Option(..., "--auth", "-a", help="Path to clouds.yaml or auth.json", exists=True, dir_okay=False),
    output: Path = typer.Option(Path("./output"), "--output", "-o", help="Directory to save exported files"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose logging"),
):
    """
    Extracts data from OpenStack and delivers it to configured destinations.
    """
    # 1. UI: Welcome Panel
    console.print(Panel.fit(
        "[bold cyan]OSI Dump v2[/bold cyan]\n[dim]OpenStack Intelligence Dumper[/dim]",
        border_style="cyan"
    ))

    # 2. Setup Logging
    setup_logging(verbose)

    try:
        # 3. Execution with Spinner
        with console.status("[bold green]Running extraction pipeline...[/bold green]", spinner="dots") as status:
            orchestrator = DumpOrchestrator(
                config_path=config,
                auth_file=auth,
                output_dir=output
            )
            
            status.update("[bold green]Processing resources...[/bold green]")
            generated_files = orchestrator.execute()

        # 4. Success Summary
        if generated_files:
            summary_tree = Tree("[bold green]Extraction Complete[/bold green]")
            
            files_branch = summary_tree.add(f"Generated {len(generated_files)} files in [bold]{output}[/bold]")
            for f in generated_files:
                files_branch.add(f"[cyan]{f.name}[/cyan]")
            
            console.print("\n")
            console.print(summary_tree)
            console.print(Panel("[bold green]SUCCESS[/bold green]", border_style="green"))
        else:
            console.print(Panel("[bold yellow]No files were generated.[/bold yellow]", border_style="yellow"))

    except Exception as e:
        # 5. Error Handling with Rich
        console.print("\n")
        console.print(Panel(f"[bold red]CRITICAL ERROR[/bold red]\n{str(e)}", border_style="red"))
        if verbose:
            console.print_exception()
        sys.exit(1)

if __name__ == "__main__":
    app()