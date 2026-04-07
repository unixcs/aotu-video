from pathlib import Path


def project_root(workspace: Path, slug: str) -> Path:
    return workspace / "projects" / slug


def ensure_project_layout(workspace: Path, slug: str) -> Path:
    root = project_root(workspace, slug)
    for path in [
        root,
        root / "shots",
        root / "outputs",
        root / "logs",
        root / "previews",
    ]:
        path.mkdir(parents=True, exist_ok=True)
    return root


def ensure_shot_layout(workspace: Path, slug: str, shot_no: str) -> Path:
    root = project_root(workspace, slug) / "shots" / shot_no
    for path in [
        root,
        root / "imports",
        root / "generated",
        root / "normalized",
        root / "audio",
        root / "subtitles",
        root / "previews",
    ]:
        path.mkdir(parents=True, exist_ok=True)
    return root
