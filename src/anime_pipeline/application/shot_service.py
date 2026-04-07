from pathlib import Path
import shutil
import subprocess

from anime_pipeline.application.project_service import get_project_db_path, show_project
from anime_pipeline.config import resolve_ffmpeg_path
from anime_pipeline.domain.models import MediaAssetRecord, ShotRecord
from anime_pipeline.infrastructure.db.repositories import (
    MediaAssetRepository,
    ShotRepository,
)
from anime_pipeline.infrastructure.filesystem.project_layout import ensure_shot_layout


def add_shot(
    workspace: Path,
    project_slug: str,
    shot_no: str,
    title: str,
    prompt_text: str,
    script_text: str,
    duration: int,
) -> ShotRecord:
    db_path = get_project_db_path(workspace, project_slug)
    ensure_shot_layout(workspace, project_slug, shot_no)
    record = ShotRecord(
        shot_no=shot_no,
        title=title,
        prompt_text=prompt_text,
        script_text=script_text,
        target_duration=duration,
    )
    ShotRepository(db_path).insert(record)
    return record


def list_shots(workspace: Path, project_slug: str) -> list[ShotRecord]:
    repository = ShotRepository(get_project_db_path(workspace, project_slug))
    return repository.list_all()


def show_shot(workspace: Path, project_slug: str, shot_no: str) -> dict[str, str | int]:
    db_path = get_project_db_path(workspace, project_slug)
    shot = ShotRepository(db_path).get(shot_no)
    shot_root = workspace / "projects" / project_slug / "shots" / shot_no

    return {
        "shot_no": shot.shot_no,
        "title": shot.title,
        "prompt": shot.prompt_text,
        "script": shot.script_text,
        "target_duration": shot.target_duration,
        "pipeline_status": shot.pipeline_status,
        "review_status": shot.review_status,
        "normalized_video": str(shot_root / "normalized" / "clip.mp4"),
        "audio_file": str(shot_root / "audio" / "voice.wav"),
        "subtitle_file": str(shot_root / "subtitles" / "subtitles.srt"),
    }


def shot_status(
    workspace: Path, project_slug: str, shot_no: str
) -> dict[str, str | int]:
    db_path = get_project_db_path(workspace, project_slug)
    shot = ShotRepository(db_path).get(shot_no)
    shot_root = workspace / "projects" / project_slug / "shots" / shot_no

    normalized_video = shot_root / "normalized" / "clip.mp4"
    audio_file = shot_root / "audio" / "voice.wav"
    subtitle_file = shot_root / "subtitles" / "subtitles.srt"

    return {
        "shot_no": shot.shot_no,
        "pipeline_status": shot.pipeline_status,
        "review_status": shot.review_status,
        "has_normalized_video": str(normalized_video.exists()).lower(),
        "has_audio": str(audio_file.exists()).lower(),
        "has_subtitles": str(subtitle_file.exists()).lower(),
    }


def import_shot_video(
    workspace: Path,
    project_slug: str,
    shot_no: str,
    source_file: Path,
) -> None:
    db_path = get_project_db_path(workspace, project_slug)
    shot_repository = ShotRepository(db_path)
    if not source_file.exists():
        raise ValueError(f"Video file '{source_file}' does not exist.")
    if not shot_repository.exists(shot_no):
        raise ValueError(
            f"Shot '{shot_no}' does not exist in project '{project_slug}'."
        )

    shot_root = workspace / "projects" / project_slug / "shots" / shot_no
    if not shot_root.exists():
        raise ValueError(
            f"Shot '{shot_no}' does not exist in project '{project_slug}'."
        )

    imported_file = shot_root / "imports" / source_file.name
    normalized_file = shot_root / "normalized" / "clip.mp4"
    shutil.copy2(source_file, imported_file)
    project_metadata = show_project(workspace, project_slug)
    _normalize_video(imported_file, normalized_file, str(project_metadata["ratio"]))

    _record_import_assets(db_path, shot_no, imported_file, normalized_file)


def _record_import_assets(
    db_path: Path,
    shot_no: str,
    imported_file: Path,
    normalized_file: Path,
) -> None:
    asset_repository = MediaAssetRepository(db_path)
    asset_repository.insert(
        shot_no,
        MediaAssetRecord(asset_type="imported_video", file_path=imported_file),
    )
    asset_repository.insert(
        shot_no,
        MediaAssetRecord(asset_type="normalized_video", file_path=normalized_file),
    )
    ShotRepository(db_path).update_pipeline_status(shot_no, "video_ready")


def _normalize_video(source_file: Path, output_file: Path, ratio: str) -> None:
    ffmpeg_path = resolve_ffmpeg_path()
    output_file.parent.mkdir(parents=True, exist_ok=True)
    width, height = _resolve_target_size(ratio)
    try:
        subprocess.run(
            [
                str(ffmpeg_path),
                "-y",
                "-i",
                str(source_file),
                "-vf",
                f"scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,fps=30",
                "-c:v",
                "mpeg4",
                "-pix_fmt",
                "yuv420p",
                "-c:a",
                "aac",
                "-ar",
                "48000",
                str(output_file),
            ],
            check=True,
            capture_output=True,
        )
    except FileNotFoundError as exc:
        raise ValueError(f"FFmpeg not found: {ffmpeg_path}") from exc
    except subprocess.CalledProcessError as exc:
        stderr = exc.stderr.decode("utf-8", errors="replace").strip()
        raise ValueError(f"Video normalization failed: {stderr}") from exc


def scan_shot_imports(workspace: Path, project_slug: str) -> int:
    db_path = get_project_db_path(workspace, project_slug)
    shot_repository = ShotRepository(db_path)
    shots_root = workspace / "projects" / project_slug / "shots"
    imported_count = 0
    supported_suffixes = {".mp4", ".mov", ".mkv", ".webm"}

    for shot_root in sorted(shots_root.iterdir()):
        if not shot_root.is_dir():
            continue
        imports_dir = shot_root / "imports"
        if not imports_dir.exists() or not imports_dir.is_dir():
            continue
        candidates = sorted(
            path
            for path in imports_dir.iterdir()
            if path.is_file() and path.suffix.lower() in supported_suffixes
        )
        if not candidates:
            continue
        if not shot_repository.exists(shot_root.name):
            raise ValueError(f"Shot '{shot_root.name}' does not exist.")

        normalized_file = shot_root / "normalized" / "clip.mp4"
        if normalized_file.exists():
            continue

        project_metadata = show_project(workspace, project_slug)
        _normalize_video(candidates[0], normalized_file, str(project_metadata["ratio"]))
        _record_import_assets(db_path, shot_root.name, candidates[0], normalized_file)
        imported_count += 1

    return imported_count


def _resolve_target_size(ratio: str) -> tuple[int, int]:
    if ratio == "9:16":
        return 720, 1280
    if ratio == "16:9":
        return 1280, 720
    if ratio == "1:1":
        return 1080, 1080
    raise ValueError(f"Unsupported project ratio '{ratio}'.")
