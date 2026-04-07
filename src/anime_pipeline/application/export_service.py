import shutil
import subprocess
from pathlib import Path

from anime_pipeline.application.project_service import get_project_db_path
from anime_pipeline.application.shot_service import list_shots
from anime_pipeline.config import resolve_ffmpeg_path


def export_rough_cut(workspace: Path, project_slug: str) -> Path:
    project_root = workspace / "projects" / project_slug
    get_project_db_path(workspace, project_slug)

    ready_clips = _collect_exportable_clips(workspace, project_slug)

    if not ready_clips:
        raise ValueError(f"No ready shot clips found for project '{project_slug}'.")

    output_path = project_root / "outputs" / "rough_cut.mp4"
    _concat_clips(
        ready_clips, project_root / "outputs" / "rough_cut_concat.txt", output_path
    )

    return output_path


def export_final(workspace: Path, project_slug: str) -> Path:
    project_root = workspace / "projects" / project_slug
    get_project_db_path(workspace, project_slug)

    shots = list_shots(workspace, project_slug)
    burned_clips: list[Path] = []
    ffmpeg_path = resolve_ffmpeg_path()
    missing_resources: list[str] = []

    exportable_shots = [
        shot for shot in shots if shot.pipeline_status == "subtitle_ready"
    ]
    in_progress_shots = [
        shot
        for shot in shots
        if shot.pipeline_status not in {"draft", "subtitle_ready"}
    ]

    for shot in exportable_shots:
        clip_path = project_root / "shots" / shot.shot_no / "normalized" / "clip.mp4"
        audio_path = project_root / "shots" / shot.shot_no / "audio" / "voice.wav"
        subtitle_path = (
            project_root / "shots" / shot.shot_no / "subtitles" / "subtitles.srt"
        )
        if not clip_path.exists():
            missing_resources.append(
                f"{shot.shot_no}: missing {clip_path.name} at {clip_path}"
            )
        if not subtitle_path.exists():
            missing_resources.append(
                f"{shot.shot_no}: missing {subtitle_path.name} at {subtitle_path}"
            )
        if not audio_path.exists():
            missing_resources.append(
                f"{shot.shot_no}: missing {audio_path.name} at {audio_path}"
            )
        if (
            not clip_path.exists()
            or not subtitle_path.exists()
            or not audio_path.exists()
        ):
            continue

        burned_output = project_root / "outputs" / f"{shot.shot_no}_subtitled.mp4"
        _mux_subtitles(ffmpeg_path, clip_path, audio_path, subtitle_path, burned_output)
        burned_clips.append(burned_output)

    if missing_resources:
        raise ValueError(
            "Final export blocked by missing resources:\n"
            + "\n".join(missing_resources)
        )

    if not burned_clips:
        if in_progress_shots:
            in_progress_summary = ", ".join(
                f"{shot.shot_no} ({shot.pipeline_status})" for shot in in_progress_shots
            )
            raise ValueError(
                f"No subtitle-ready shots found for final export in project '{project_slug}'. "
                f"In-progress non-draft shots: {in_progress_summary}."
            )
        raise ValueError(
            f"No non-draft shots are ready for final export in project '{project_slug}'."
        )

    output_path = project_root / "outputs" / "final.mp4"
    _concat_clips(
        burned_clips, project_root / "outputs" / "final_concat.txt", output_path
    )
    return output_path


def _collect_exportable_clips(workspace: Path, project_slug: str) -> list[Path]:
    project_root = workspace / "projects" / project_slug
    ready_clips: list[Path] = []
    for shot in list_shots(workspace, project_slug):
        clip_path = project_root / "shots" / shot.shot_no / "normalized" / "clip.mp4"
        if clip_path.exists():
            ready_clips.append(clip_path)
    return ready_clips


def _concat_clips(clips: list[Path], concat_file: Path, output_path: Path) -> None:
    concat_file.write_text(
        "".join(f"file '{_escape_concat_path(clip.resolve())}'\n" for clip in clips),
        encoding="utf-8",
    )

    ffmpeg_path = resolve_ffmpeg_path()
    try:
        subprocess.run(
            [
                str(ffmpeg_path),
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(concat_file),
                "-map",
                "0",
                "-c:v",
                "mpeg4",
                "-c:a",
                "aac",
                "-c:s",
                "mov_text",
                "-movflags",
                "+faststart",
                str(output_path),
            ],
            check=True,
            capture_output=True,
        )
    except FileNotFoundError as exc:
        raise ValueError(f"FFmpeg not found: {ffmpeg_path}") from exc
    except subprocess.CalledProcessError as exc:
        stderr = exc.stderr.decode("utf-8", errors="replace").strip()
        raise ValueError(f"FFmpeg export failed: {stderr}") from exc


def _mux_subtitles(
    ffmpeg_path: Path,
    clip_path: Path,
    audio_path: Path,
    subtitle_path: Path,
    output_path: Path,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        command = [
            str(ffmpeg_path),
            "-y",
            "-i",
            str(clip_path),
        ]
        if audio_path.exists():
            command.extend(["-i", str(audio_path)])
        command.extend(["-i", str(subtitle_path)])
        command.extend(
            [
                "-c:v",
                "copy",
                "-c:a",
                "aac",
                "-c:s",
                "mov_text",
                "-map",
                "0:v:0",
            ]
        )
        if audio_path.exists():
            command.extend(["-map", "1:a:0", "-map", "2:s:0"])
        else:
            command.extend(["-map", "0:a?", "-map", "1:s:0"])
        command.append(str(output_path))

        subprocess.run(
            command,
            check=True,
            capture_output=True,
        )
    except FileNotFoundError as exc:
        raise ValueError(f"FFmpeg not found: {ffmpeg_path}") from exc
    except subprocess.CalledProcessError as exc:
        stderr = exc.stderr.decode("utf-8", errors="replace").strip()
        raise ValueError(f"FFmpeg export failed: {stderr}") from exc


def _escape_concat_path(path: Path) -> str:
    return path.as_posix().replace("'", r"'\''")
