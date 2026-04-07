from pathlib import Path
import hashlib
import re

import yaml

from anime_pipeline.config import validate_project_ratio
from anime_pipeline.domain.models import ProjectRecord
from anime_pipeline.infrastructure.db.repositories import (
    ProjectRepository,
    ShotRepository,
)
from anime_pipeline.infrastructure.db.schema import initialize_database
from anime_pipeline.infrastructure.filesystem.project_layout import (
    ensure_project_layout,
)


def slugify_project_name(name: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", name.strip().lower())
    normalized = normalized.strip("-")
    if normalized:
        return normalized

    digest = hashlib.sha1(name.encode("utf-8")).hexdigest()[:8]
    return f"project-{digest}"


def create_project(
    workspace: Path, name: str, ratio: str, duration: int
) -> ProjectRecord:
    ratio = validate_project_ratio(ratio)
    slug = slugify_project_name(name)
    root = ensure_project_layout(workspace, slug)
    db_path = root / "project.db"
    if db_path.exists():
        existing_records = ProjectRepository(db_path).list_all()
        if any(record.slug == slug for record in existing_records):
            raise ValueError(f"Project '{slug}' already exists.")
    initialize_database(db_path)
    record = ProjectRecord(name=name, slug=slug, ratio=ratio, target_duration=duration)
    ProjectRepository(db_path).insert(record)
    project_file = root / "project.yaml"
    project_file.write_text(
        yaml.safe_dump(
            {
                "name": name,
                "slug": slug,
                "ratio": ratio,
                "target_duration": duration,
            },
            allow_unicode=True,
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    return record


def list_projects(workspace: Path) -> list[ProjectRecord]:
    projects_root = workspace / "projects"
    if not projects_root.exists():
        return []

    records: list[ProjectRecord] = []
    for candidate in sorted(projects_root.iterdir()):
        db_path = candidate / "project.db"
        if db_path.exists():
            records.extend(ProjectRepository(db_path).list_all())
    return records


def get_project_db_path(workspace: Path, project_slug: str) -> Path:
    db_path = workspace / "projects" / project_slug / "project.db"
    if not db_path.exists():
        raise ValueError(f"Project '{project_slug}' does not exist.")
    return db_path


def show_project(workspace: Path, project_slug: str) -> dict[str, str | int]:
    project_file = workspace / "projects" / project_slug / "project.yaml"
    if not project_file.exists():
        raise ValueError(f"Project '{project_slug}' does not exist.")
    return yaml.safe_load(project_file.read_text(encoding="utf-8"))


def project_status(workspace: Path, project_slug: str) -> dict[str, str | int]:
    metadata = show_project(workspace, project_slug)
    db_path = get_project_db_path(workspace, project_slug)
    shots = ShotRepository(db_path).list_all()
    pipeline_counts: dict[str, int] = {}
    for shot in shots:
        pipeline_counts[shot.pipeline_status] = (
            pipeline_counts.get(shot.pipeline_status, 0) + 1
        )

    result: dict[str, str | int] = {
        "project": str(metadata["slug"]),
        "total_shots": len(shots),
    }
    for status, count in sorted(pipeline_counts.items()):
        result[status] = count
    return result
