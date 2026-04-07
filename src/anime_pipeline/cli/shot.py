from pathlib import Path

import typer

from anime_pipeline.application.shot_service import (
    add_shot,
    import_shot_video,
    list_shots,
    scan_shot_imports,
    shot_status,
    show_shot,
)
from anime_pipeline.config import DEFAULT_WORKSPACE

app = typer.Typer(help="Manage shots.")


@app.command("add")
def add(
    project: str = typer.Option(..., "--project", help="Project slug."),
    shot: str = typer.Option(..., "--shot", help="Shot identifier."),
    title: str = typer.Option(..., "--title", help="Shot title."),
    prompt: str = typer.Option(..., "--prompt", help="Prompt text."),
    script: str = typer.Option(..., "--script", help="Narration/script text."),
    duration: int = typer.Option(
        ..., "--duration", help="Target shot duration in seconds."
    ),
    workspace: Path = typer.Option(
        DEFAULT_WORKSPACE, "--workspace", help="Workspace root path."
    ),
) -> None:
    try:
        record = add_shot(
            workspace=workspace,
            project_slug=project,
            shot_no=shot,
            title=title,
            prompt_text=prompt,
            script_text=script,
            duration=duration,
        )
    except ValueError as exc:
        typer.echo(str(exc))
        raise typer.Exit(code=1) from exc

    typer.echo(f"Added shot {record.shot_no}")


@app.command("list")
def list_command(
    project: str = typer.Option(..., "--project", help="Project slug."),
    workspace: Path = typer.Option(
        DEFAULT_WORKSPACE, "--workspace", help="Workspace root path."
    ),
) -> None:
    try:
        records = list_shots(workspace=workspace, project_slug=project)
    except ValueError as exc:
        typer.echo(str(exc))
        raise typer.Exit(code=1) from exc

    for record in records:
        typer.echo(f"{record.shot_no}\t{record.title}\t{record.pipeline_status}")


@app.command("import-video")
def import_video(
    project: str = typer.Option(..., "--project", help="Project slug."),
    shot: str = typer.Option(..., "--shot", help="Shot identifier."),
    file: Path = typer.Option(..., "--file", help="Source video file path."),
    workspace: Path = typer.Option(
        DEFAULT_WORKSPACE, "--workspace", help="Workspace root path."
    ),
) -> None:
    try:
        import_shot_video(
            workspace=workspace,
            project_slug=project,
            shot_no=shot,
            source_file=file,
        )
    except ValueError as exc:
        typer.echo(str(exc))
        raise typer.Exit(code=1) from exc

    typer.echo(f"Imported video for {shot}")


@app.command("scan-imports")
def scan_imports(
    project: str = typer.Option(..., "--project", help="Project slug."),
    workspace: Path = typer.Option(
        DEFAULT_WORKSPACE, "--workspace", help="Workspace root path."
    ),
) -> None:
    try:
        imported_count = scan_shot_imports(workspace=workspace, project_slug=project)
    except ValueError as exc:
        typer.echo(str(exc))
        raise typer.Exit(code=1) from exc

    typer.echo(f"Imported {imported_count} shot(s).")


@app.command("show")
def show(
    project: str = typer.Option(..., "--project", help="Project slug."),
    shot: str = typer.Option(..., "--shot", help="Shot identifier."),
    workspace: Path = typer.Option(
        DEFAULT_WORKSPACE, "--workspace", help="Workspace root path."
    ),
) -> None:
    try:
        metadata = show_shot(workspace=workspace, project_slug=project, shot_no=shot)
    except ValueError as exc:
        typer.echo(str(exc))
        raise typer.Exit(code=1) from exc

    for key, value in metadata.items():
        typer.echo(f"{key}: {value}")


@app.command("status")
def status(
    project: str = typer.Option(..., "--project", help="Project slug."),
    shot: str = typer.Option(..., "--shot", help="Shot identifier."),
    workspace: Path = typer.Option(
        DEFAULT_WORKSPACE, "--workspace", help="Workspace root path."
    ),
) -> None:
    try:
        metadata = shot_status(workspace=workspace, project_slug=project, shot_no=shot)
    except ValueError as exc:
        typer.echo(str(exc))
        raise typer.Exit(code=1) from exc

    for key, value in metadata.items():
        typer.echo(f"{key}: {value}")
