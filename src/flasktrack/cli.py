"""CLI interface for FlaskTrack."""

from pathlib import Path

import typer
from cookiecutter.main import cookiecutter
from rich import print
from rich.console import Console
from rich.table import Table

from flasktrack import __version__
from flasktrack.tracker import FlaskTracker
from flasktrack.utils import add_user_to_app

app = typer.Typer(
    name="flasktrack",
    help="Track and analyze Flask applications",
    add_completion=False,
)
console = Console()


@app.command()
def routes(
    app_path: Path | None = typer.Argument(
        None,
        help="Path to the Flask application file or module",
    ),
):
    """List all routes in a Flask application."""
    if app_path is None:
        console.print("[bold red]Error:[/bold red] Missing argument 'APP_PATH'.")
        console.print("\n[bold cyan]Usage:[/bold cyan] flasktrack routes [APP_PATH]")
        console.print("\nList all routes in a Flask application.")
        console.print("\n[bold cyan]Arguments:[/bold cyan]")
        console.print("  APP_PATH  Path to the Flask application file or module")
        console.print("\n[bold cyan]Options:[/bold cyan]")
        console.print("  --help    Show this message and exit.")
        raise typer.Exit(1)

    if not app_path.exists():
        console.print(f"[bold red]Error:[/bold red] Path '{app_path}' does not exist.")
        raise typer.Exit(1)

    console.print("[bold cyan]Flask Routes[/bold cyan] 📍")

    tracker = FlaskTracker(app_path, verbose=False)
    routes_list = tracker.get_routes()

    table = Table(title="Application Routes")
    table.add_column("Endpoint", style="cyan")
    table.add_column("Methods", style="yellow")
    table.add_column("Rule", style="green")

    for route in routes_list:
        table.add_row(route["endpoint"], ", ".join(route["methods"]), route["rule"])

    console.print(table)


@app.command()
def init(
    project_name: str | None = typer.Argument(
        None,
        help="Name of the Flask project to create, or '.' to use current directory name",
    ),
    directory: Path | None = typer.Option(
        None,
        "--dir",
        "-d",
        help="Directory to create the project in (defaults to current directory)",
    ),
):
    """Initialize a new Flask application with authentication and best practices."""
    if project_name is None:
        console.print("[bold red]Error:[/bold red] Missing argument 'PROJECT_NAME'.")
        console.print("\n[bold cyan]Usage:[/bold cyan] flasktrack init [PROJECT_NAME]")
        console.print(
            "\nInitialize a new Flask application with authentication and best practices."
        )
        console.print("\n[bold cyan]Arguments:[/bold cyan]")
        console.print(
            "  PROJECT_NAME  Name of the Flask project to create, or '.' to use current directory name"
        )
        console.print("\n[bold cyan]Options:[/bold cyan]")
        console.print(
            "  -d, --dir PATH  Directory to create the project in (defaults to current directory)"
        )
        console.print("  --help          Show this message and exit.")
        console.print("\n[bold cyan]Examples:[/bold cyan]")
        console.print('  flasktrack init "My New App"')
        console.print("  flasktrack init .  # Use current directory name")
        raise typer.Exit(1)

    # Handle special case where user passes '.' to use current directory name
    if project_name == ".":
        project_name = Path.cwd().name
        console.print(
            f"[bold yellow]Using current directory name:[/bold yellow] {project_name}"
        )

    console.print(
        f"[bold green]Creating Flask application:[/bold green] {project_name} 🚀"
    )

    # Get the template directory
    template_dir = Path(__file__).parent / "templates" / "flask-app"

    if not template_dir.exists():
        console.print(
            f"[bold red]Error:[/bold red] Template directory not found at {template_dir}"
        )
        raise typer.Exit(1)

    # Set output directory
    if directory:
        # When a specific directory is provided, we want to create the project IN that directory
        # not as a subdirectory of it. So we'll use the parent as output_dir and the
        # directory name as the project_slug
        output_dir = directory.parent if directory.parent else Path.cwd()
        project_slug = directory.name
        extra_context = {
            "project_name": project_name,
            "project_slug": project_slug,
        }
    else:
        # Default behavior - create in current directory with auto-generated slug
        output_dir = Path.cwd()
        extra_context = {
            "project_name": project_name,
        }

    try:
        # Run cookiecutter
        project_path = cookiecutter(
            str(template_dir),
            output_dir=str(output_dir),
            no_input=True,
            extra_context=extra_context,
        )

        console.print(f"[bold green]✓[/bold green] Project created at: {project_path}")
        console.print("\n[bold cyan]Next steps:[/bold cyan]")

        # Get the relative path if possible, otherwise use absolute
        try:
            cd_path = Path(project_path).relative_to(Path.cwd())
        except ValueError:
            # Project is not in a subdirectory of cwd, use absolute path
            cd_path = Path(project_path)

        console.print(f"  1. cd {cd_path}")
        console.print("  2. just install  # Sets up everything for development")
        console.print("  3. just run      # Start the development server")
        console.print("\n[bold green]Your Flask app is ready![/bold green] 🎉")

    except Exception as e:
        console.print(f"[bold red]Error creating project:[/bold red] {str(e)}")
        raise typer.Exit(1) from e


@app.command()
def add_user(
    username: str = typer.Argument(..., help="Username for the new user"),
    email: str = typer.Argument(..., help="Email address for the new user"),
    password: str | None = typer.Option(
        None,
        "--password",
        "-p",
        help="Password for the new user (will prompt if not provided)",
    ),
    app_path: Path = typer.Option(
        Path.cwd(),
        "--app-path",
        "-a",
        help="Path to the Flask application directory",
    ),
):
    """Add a new user to a Flask application created with 'ft init'."""
    console.print(f"[bold cyan]Adding user:[/bold cyan] {username}")

    # Check if the app_path contains a Flask app
    app_file = app_path / "app.py"
    if not app_file.exists():
        console.print(
            f"[bold red]Error:[/bold red] No Flask application found at {app_path}"
        )
        console.print(
            "Make sure you're in a directory created with 'ft init' or specify --app-path"
        )
        raise typer.Exit(1)

    # Check if the app directory exists
    app_dir = app_path / "app"
    if not app_dir.exists():
        console.print(
            f"[bold red]Error:[/bold red] No 'app' directory found at {app_path}"
        )
        console.print("This doesn't appear to be a Flask app created with 'ft init'")
        raise typer.Exit(1)

    # If password not provided, prompt for it
    if password is None:
        password = typer.prompt("Password", hide_input=True, confirmation_prompt=True)

    try:
        # Add the user to the database
        success = add_user_to_app(
            app_path=app_path, username=username, email=email, password=password
        )

        if success:
            console.print(
                f"[bold green]✓[/bold green] User '{username}' added successfully!"
            )
            console.print(f"  Email: {email}")
            console.print(
                "\n[bold cyan]User can now log in to the application![/bold cyan]"
            )
        else:
            console.print(
                "[bold red]Error:[/bold red] Failed to add user. User might already exist."
            )
            raise typer.Exit(1)

    except Exception as e:
        console.print(f"[bold red]Error adding user:[/bold red] {str(e)}")
        raise typer.Exit(1) from e


@app.command()
def version():
    """Show the version of FlaskTrack."""
    print(__version__)


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
):
    """FlaskTrack - A CLI tool for tracking and analyzing Flask applications."""
    if ctx.invoked_subcommand is None:
        console.print(
            "[bold cyan]FlaskTrack[/bold cyan] - A Rails-inspired Flask framework with scaffolding"
        )
        console.print(f"Version: [bold green]{__version__}[/bold green]\n")
        console.print("[bold cyan]Usage:[/bold cyan] flasktrack [COMMAND]")
        console.print("\n[bold cyan]Commands:[/bold cyan]")
        console.print(
            "  [bold green]init[/bold green]      Initialize a new Flask application"
        )
        console.print(
            "  [bold magenta]add-user[/bold magenta]  Add a user to a Flask application"
        )
        console.print(
            "  [bold blue]routes[/bold blue]    List all routes in a Flask application"
        )
        console.print("  [bold yellow]version[/bold yellow]   Show version information")
        console.print("\n[bold cyan]Examples:[/bold cyan]")
        console.print('  flasktrack init "My New App"')
        console.print("  flasktrack init .  # Uses current directory name")
        console.print("  flasktrack add-user john john@example.com")
        console.print("  flasktrack routes app.py")
        console.print(
            "\nRun '[bold cyan]flasktrack [COMMAND] --help[/bold cyan]' for more information on a command."
        )


if __name__ == "__main__":
    app()
