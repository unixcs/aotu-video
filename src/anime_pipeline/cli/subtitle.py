from pathlib import Path

import typer

from anime_pipeline.application.subtitle_service import generate_subtitles
from anime_pipeline.config import DEFAULT_WORKSPACE

app = typer.Typer(help="Generate subtitle assets.")


@app.command("generate")
def generate(
    project: str = typer.Option(..., "--project", help="Project slug."),
    workspace: Path = typer.Option(
        DEFAULT_WORKSPACE, "--workspace", help="Workspace root path."
    ),
) -> None:
    try:
        generated_count = generate_subtitles(workspace=workspace, project_slug=project)
    except ValueError as exc:
        typer.echo(str(exc))
        raise typer.Exit(code=1) from exc

    typer.echo(f"Generated subtitles for {generated_count} shot(s).")
