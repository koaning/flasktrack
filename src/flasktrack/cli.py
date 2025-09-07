"""CLI interface for FlaskTrack."""

from pathlib import Path
from typing import Optional

import typer
from rich import print
from rich.console import Console
from rich.table import Table

from flasktrack import __version__
from flasktrack.tracker import FlaskTracker

app = typer.Typer(
    name="flasktrack",
    help="Track and analyze Flask applications",
    add_completion=False,
)
console = Console()


@app.command()
def track(
    app_path: Path = typer.Argument(
        ...,
        help="Path to the Flask application file or module",
        exists=True,
    ),
    host: str = typer.Option(
        "127.0.0.1",
        "--host",
        "-h",
        help="Host to track the Flask app on",
    ),
    port: int = typer.Option(
        5000,
        "--port",
        "-p",
        help="Port to track the Flask app on",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose output",
    ),
):
    """Track a Flask application's endpoints and performance."""
    console.print(f"[bold green]Starting FlaskTrack[/bold green] 🚀")
    console.print(f"Tracking app at: {app_path}")
    
    tracker = FlaskTracker(app_path, verbose=verbose)
    tracker.start_tracking(host=host, port=port)


@app.command()
def analyze(
    app_path: Path = typer.Argument(
        ...,
        help="Path to the Flask application file or module",
        exists=True,
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output file for analysis report",
    ),
):
    """Analyze a Flask application's structure and endpoints."""
    console.print(f"[bold blue]Analyzing Flask application[/bold blue] 🔍")
    console.print(f"Application: {app_path}")
    
    tracker = FlaskTracker(app_path, verbose=False)
    analysis = tracker.analyze()
    
    table = Table(title="Flask Application Analysis")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    
    for key, value in analysis.items():
        table.add_row(key, str(value))
    
    console.print(table)
    
    if output:
        tracker.save_analysis(analysis, output)
        console.print(f"[green]Analysis saved to {output}[/green]")


@app.command()
def routes(
    app_path: Path = typer.Argument(
        ...,
        help="Path to the Flask application file or module",
        exists=True,
    ),
):
    """List all routes in a Flask application."""
    console.print(f"[bold cyan]Flask Routes[/bold cyan] 📍")
    
    tracker = FlaskTracker(app_path, verbose=False)
    routes_list = tracker.get_routes()
    
    table = Table(title="Application Routes")
    table.add_column("Endpoint", style="cyan")
    table.add_column("Methods", style="yellow")
    table.add_column("Rule", style="green")
    
    for route in routes_list:
        table.add_row(
            route["endpoint"],
            ", ".join(route["methods"]),
            route["rule"]
        )
    
    console.print(table)


@app.command()
def version():
    """Show the version of FlaskTrack."""
    print(f"[bold cyan]FlaskTrack[/bold cyan] version [bold green]{__version__}[/bold green]")


@app.callback()
def main(
    ctx: typer.Context,
):
    """FlaskTrack - A CLI tool for tracking and analyzing Flask applications."""
    pass


if __name__ == "__main__":
    app()