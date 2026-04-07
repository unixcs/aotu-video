import math
from pathlib import Path
import re

from anime_pipeline.application.project_service import get_project_db_path
from anime_pipeline.domain.models import MediaAssetRecord
from anime_pipeline.infrastructure.db.repositories import (
    MediaAssetRepository,
    ShotRepository,
)


def generate_subtitles(workspace: Path, project_slug: str) -> int:
    db_path = get_project_db_path(workspace, project_slug)
    shot_repository = ShotRepository(db_path)
    asset_repository = MediaAssetRepository(db_path)
    generated_count = 0

    for shot in shot_repository.list_by_pipeline_status("audio_ready"):
        shot_root = workspace / "projects" / project_slug / "shots" / shot.shot_no
        subtitle_file = shot_root / "subtitles" / "subtitles.srt"
        subtitle_file.parent.mkdir(parents=True, exist_ok=True)
        total_duration_ms = max(1000, shot.target_duration * 1000)
        subtitle_file.write_text(
            _build_srt(shot.script_text, total_duration_ms),
            encoding="utf-8",
        )
        asset_repository.insert(
            shot.shot_no,
            MediaAssetRecord(asset_type="subtitle_file", file_path=subtitle_file),
        )
        shot_repository.update_pipeline_status(shot.shot_no, "subtitle_ready")
        generated_count += 1

    return generated_count


def _build_srt(script_text: str, total_duration_ms: int) -> str:
    cues = _split_script(script_text)
    if not cues:
        cues = [script_text.strip()]

    weights = [_cue_weight(cue) for cue in cues]
    total_weight = sum(weights)
    lines: list[str] = []
    current_ms = 0
    for index, cue in enumerate(cues, start=1):
        start_ms = current_ms
        if index == len(cues):
            end_ms = total_duration_ms
        else:
            current_weight = sum(weights[:index])
            end_ms = int(math.floor(total_duration_ms * current_weight / total_weight))
        current_ms = end_ms
        lines.extend(
            [
                str(index),
                f"{_format_srt_time(start_ms)} --> {_format_srt_time(end_ms)}",
                cue,
                "",
            ]
        )
    return "\n".join(lines)


def _split_script(script_text: str) -> list[str]:
    parts = re.findall(r".*?[。！？!?；;，,](?:\s*|$)|.+$", script_text.strip())
    return [part.strip() for part in parts if part.strip()]


def _cue_weight(cue: str) -> int:
    normalized = re.sub(r"[\s。！？!?；;，,、：:\.\-—…'\"()（）\[\]【】{}]", "", cue)
    return max(1, len(normalized))


def _format_srt_time(total_ms: int) -> str:
    hours, remainder = divmod(total_ms, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    seconds, milliseconds = divmod(remainder, 1_000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"
