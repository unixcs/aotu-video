from pathlib import Path

import typer

from anime_pipeline.application.audio_service import generate_audio
from anime_pipeline.config import DEFAULT_WORKSPACE

app = typer.Typer(help="Generate audio assets.")


@app.command("generate")
def generate(
    project: str = typer.Option(..., "--project", help="Project slug."),
    provider: str | None = typer.Option(None, "--provider", help="TTS provider name."),
    workspace: Path = typer.Option(
        DEFAULT_WORKSPACE, "--workspace", help="Workspace root path."
    ),
) -> None:
    try:
        generated_count, provider_name = generate_audio(
            workspace=workspace,
            project_slug=project,
            provider_name=provider,
        )
    except ValueError as exc:
        typer.echo(str(exc))
        raise typer.Exit(code=1) from exc

    typer.echo(f"Generated audio for {generated_count} shot(s) using {provider_name}.")
