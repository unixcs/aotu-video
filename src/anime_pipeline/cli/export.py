from pathlib import Path

import typer

from anime_pipeline.application.export_service import export_final, export_rough_cut
from anime_pipeline.config import DEFAULT_WORKSPACE

app = typer.Typer(help="Export project outputs.")


@app.command("rough-cut")
def rough_cut(
    project: str = typer.Option(..., "--project", help="Project slug."),
    workspace: Path = typer.Option(
        DEFAULT_WORKSPACE, "--workspace", help="Workspace root path."
    ),
) -> None:
    try:
        output_path = export_rough_cut(workspace=workspace, project_slug=project)
    except ValueError as exc:
        typer.echo(str(exc))
        raise typer.Exit(code=1) from exc

    typer.echo(f"Exported rough cut to {output_path}")


@app.command("final")
def final(
    project: str = typer.Option(..., "--project", help="Project slug."),
    workspace: Path = typer.Option(
        DEFAULT_WORKSPACE, "--workspace", help="Workspace root path."
    ),
) -> None:
    try:
        output_path = export_final(workspace=workspace, project_slug=project)
    except ValueError as exc:
        typer.echo(str(exc))
        raise typer.Exit(code=1) from exc

    typer.echo(f"Exported final video to {output_path}")
