from pathlib import Path

import typer

from anime_pipeline.application.project_service import (
    create_project,
    list_projects,
    project_status,
    show_project,
)
from anime_pipeline.config import DEFAULT_WORKSPACE

app = typer.Typer(help="Manage projects.")


@app.command("create")
def create(
    name: str = typer.Option(..., "--name", help="Project name."),
    ratio: str = typer.Option(..., "--ratio", help="Output aspect ratio."),
    duration: int = typer.Option(
        ..., "--duration", help="Target project duration in seconds."
    ),
    workspace: Path = typer.Option(
        DEFAULT_WORKSPACE, "--workspace", help="Workspace root path."
    ),
) -> None:
    try:
        record = create_project(
            workspace=workspace, name=name, ratio=ratio, duration=duration
        )
    except ValueError as exc:
        typer.echo(str(exc))
        raise typer.Exit(code=1) from exc

    typer.echo(f"Created project {record.slug}")


@app.command("list")
def list_command(
    workspace: Path = typer.Option(
        DEFAULT_WORKSPACE, "--workspace", help="Workspace root path."
    ),
) -> None:
    for record in list_projects(workspace):
        typer.echo(
            f"{record.slug}\t{record.name}\t{record.ratio}\t{record.target_duration}"
        )


@app.command("show")
def show(
    project: str = typer.Option(..., "--project", help="Project slug."),
    workspace: Path = typer.Option(
        DEFAULT_WORKSPACE, "--workspace", help="Workspace root path."
    ),
) -> None:
    try:
        metadata = show_project(workspace=workspace, project_slug=project)
    except ValueError as exc:
        typer.echo(str(exc))
        raise typer.Exit(code=1) from exc

    for key, value in metadata.items():
        typer.echo(f"{key}: {value}")


@app.command("status")
def status(
    project: str = typer.Option(..., "--project", help="Project slug."),
    workspace: Path = typer.Option(
        DEFAULT_WORKSPACE, "--workspace", help="Workspace root path."
    ),
) -> None:
    try:
        metadata = project_status(workspace=workspace, project_slug=project)
    except ValueError as exc:
        typer.echo(str(exc))
        raise typer.Exit(code=1) from exc

    for key, value in metadata.items():
        typer.echo(f"{key}: {value}")
