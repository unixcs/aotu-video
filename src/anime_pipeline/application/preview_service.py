import os
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape

from anime_pipeline.application.project_service import get_project_db_path
from anime_pipeline.domain.models import PreviewShotRecord
from anime_pipeline.infrastructure.db.repositories import ShotRepository


def build_preview(workspace: Path, project_slug: str) -> Path:
    project_root = workspace / "projects" / project_slug
    get_project_db_path(workspace, project_slug)

    project_metadata = yaml.safe_load(
        (project_root / "project.yaml").read_text(encoding="utf-8")
    )
    shots = _collect_preview_shots(project_root)

    template_dir = (
        Path(__file__).resolve().parent.parent
        / "presentation"
        / "preview"
        / "templates"
    )
    environment = Environment(
        loader=FileSystemLoader(str(template_dir)),
        autoescape=select_autoescape(("html", "xml")),
    )
    template = environment.get_template("index.html.j2")

    output_path = project_root / "previews" / "index.html"
    output_path.write_text(
        template.render(project=project_metadata, shots=shots),
        encoding="utf-8",
    )
    return output_path


def _collect_preview_shots(project_root: Path) -> list[PreviewShotRecord]:
    repository = ShotRepository(project_root / "project.db")
    shots: list[PreviewShotRecord] = []

    for shot in repository.list_all():
        normalized_file = (
            project_root / "shots" / shot.shot_no / "normalized" / "clip.mp4"
        )
        relative_video = None
        if normalized_file.exists():
            relative_video = os.path.relpath(
                normalized_file,
                start=project_root / "previews",
            ).replace("\\", "/")
        shots.append(
            PreviewShotRecord(
                shot_no=shot.shot_no,
                title=shot.title,
                prompt_text=shot.prompt_text,
                script_text=shot.script_text,
                pipeline_status=shot.pipeline_status,
                normalized_video_path=relative_video,
            )
        )

    return shots
