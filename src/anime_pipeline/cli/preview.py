from pathlib import Path

import typer

from anime_pipeline.application.preview_service import build_preview
from anime_pipeline.config import DEFAULT_WORKSPACE

app = typer.Typer(help="Build local preview pages.")


@app.command("build")
def build(
    project: str = typer.Option(..., "--project", help="Project slug."),
    workspace: Path = typer.Option(
        DEFAULT_WORKSPACE, "--workspace", help="Workspace root path."
    ),
) -> None:
    try:
        output_path = build_preview(workspace=workspace, project_slug=project)
    except ValueError as exc:
        typer.echo(str(exc))
        raise typer.Exit(code=1) from exc

    typer.echo(f"Built preview at {output_path}")
