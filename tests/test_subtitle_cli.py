import sqlite3
from pathlib import Path
import re

from typer.testing import CliRunner

from anime_pipeline.cli.main import app
from tests.media_test_utils import create_test_video, require_ffmpeg


def _extract_srt_ranges(subtitle_text: str) -> list[tuple[str, str]]:
    return re.findall(
        r"(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})",
        subtitle_text,
    )


def _srt_time_to_ms(value: str) -> int:
    hours, minutes, seconds_millis = value.split(":")
    seconds, millis = seconds_millis.split(",")
    return (
        int(hours) * 3_600_000
        + int(minutes) * 60_000
        + int(seconds) * 1_000
        + int(millis)
    )


def test_subtitle_generate_creates_srt_asset_and_updates_status(
    tmp_path: Path, monkeypatch
) -> None:
    runner = CliRunner()
    workspace = tmp_path / "workspace"
    source_file = tmp_path / "source.mp4"
    ffmpeg_path = require_ffmpeg()
    monkeypatch.setenv("FFMPEG_PATH", ffmpeg_path)
    create_test_video(ffmpeg_path, source_file, color="red")

    create_result = runner.invoke(
        app,
        [
            "project",
            "create",
            "--workspace",
            str(workspace),
            "--name",
            "Demo Project",
            "--ratio",
            "9:16",
            "--duration",
            "60",
        ],
    )
    add_result = runner.invoke(
        app,
        [
            "shot",
            "add",
            "--workspace",
            str(workspace),
            "--project",
            "demo-project",
            "--shot",
            "shot-001",
            "--title",
            "Opening",
            "--prompt",
            "anime boy in rain",
            "--script",
            "He walks alone in the rain.",
            "--duration",
            "5",
        ],
    )
    import_result = runner.invoke(
        app,
        [
            "shot",
            "import-video",
            "--workspace",
            str(workspace),
            "--project",
            "demo-project",
            "--shot",
            "shot-001",
            "--file",
            str(source_file),
        ],
    )
    audio_result = runner.invoke(
        app,
        [
            "audio",
            "generate",
            "--workspace",
            str(workspace),
            "--project",
            "demo-project",
        ],
    )
    subtitle_result = runner.invoke(
        app,
        [
            "subtitle",
            "generate",
            "--workspace",
            str(workspace),
            "--project",
            "demo-project",
        ],
    )

    subtitle_file = (
        workspace
        / "projects"
        / "demo-project"
        / "shots"
        / "shot-001"
        / "subtitles"
        / "subtitles.srt"
    )
    connection = sqlite3.connect(workspace / "projects" / "demo-project" / "project.db")
    try:
        shot_row = connection.execute(
            "SELECT pipeline_status FROM shots WHERE shot_no = ?",
            ("shot-001",),
        ).fetchone()
        asset_rows = connection.execute(
            "SELECT asset_type, file_path FROM media_assets WHERE shot_no = ? ORDER BY id",
            ("shot-001",),
        ).fetchall()
    finally:
        connection.close()

    assert create_result.exit_code == 0
    assert add_result.exit_code == 0
    assert import_result.exit_code == 0
    assert audio_result.exit_code == 0
    assert subtitle_result.exit_code == 0
    assert subtitle_file.exists()
    assert subtitle_file.read_text(encoding="utf-8")
    assert "He walks alone in the rain." in subtitle_file.read_text(encoding="utf-8")
    assert shot_row == ("subtitle_ready",)
    assert asset_rows[-1] == ("subtitle_file", str(subtitle_file))


def test_subtitle_generate_splits_script_by_punctuation_into_multiple_cues(
    tmp_path: Path, monkeypatch
) -> None:
    runner = CliRunner()
    workspace = tmp_path / "workspace"
    source_file = tmp_path / "source.mp4"
    ffmpeg_path = require_ffmpeg()
    monkeypatch.setenv("FFMPEG_PATH", ffmpeg_path)
    create_test_video(ffmpeg_path, source_file, color="red")

    runner.invoke(
        app,
        [
            "project",
            "create",
            "--workspace",
            str(workspace),
            "--name",
            "Demo Project",
            "--ratio",
            "9:16",
            "--duration",
            "60",
        ],
    )
    runner.invoke(
        app,
        [
            "shot",
            "add",
            "--workspace",
            str(workspace),
            "--project",
            "demo-project",
            "--shot",
            "shot-001",
            "--title",
            "Opening",
            "--prompt",
            "anime boy in rain",
            "--script",
            "第一句。第二句，第三句！",
            "--duration",
            "5",
        ],
    )
    runner.invoke(
        app,
        [
            "shot",
            "import-video",
            "--workspace",
            str(workspace),
            "--project",
            "demo-project",
            "--shot",
            "shot-001",
            "--file",
            str(source_file),
        ],
    )
    runner.invoke(
        app,
        [
            "audio",
            "generate",
            "--workspace",
            str(workspace),
            "--project",
            "demo-project",
        ],
    )

    subtitle_result = runner.invoke(
        app,
        [
            "subtitle",
            "generate",
            "--workspace",
            str(workspace),
            "--project",
            "demo-project",
        ],
    )

    subtitle_file = (
        workspace
        / "projects"
        / "demo-project"
        / "shots"
        / "shot-001"
        / "subtitles"
        / "subtitles.srt"
    )
    subtitle_text = subtitle_file.read_text(encoding="utf-8")
    ranges = _extract_srt_ranges(subtitle_text)

    assert subtitle_result.exit_code == 0
    assert "第一句。" in subtitle_text
    assert "第二句，" in subtitle_text
    assert "第三句！" in subtitle_text
    assert ranges == [
        ("00:00:00,000", "00:00:01,666"),
        ("00:00:01,666", "00:00:03,333"),
        ("00:00:03,333", "00:00:05,000"),
    ]


def test_subtitle_generate_allocates_more_time_to_longer_cues(
    tmp_path: Path, monkeypatch
) -> None:
    runner = CliRunner()
    workspace = tmp_path / "workspace"
    source_file = tmp_path / "source.mp4"
    ffmpeg_path = require_ffmpeg()
    monkeypatch.setenv("FFMPEG_PATH", ffmpeg_path)
    create_test_video(ffmpeg_path, source_file, color="red")

    runner.invoke(
        app,
        [
            "project",
            "create",
            "--workspace",
            str(workspace),
            "--name",
            "Demo Project",
            "--ratio",
            "9:16",
            "--duration",
            "60",
        ],
    )
    runner.invoke(
        app,
        [
            "shot",
            "add",
            "--workspace",
            str(workspace),
            "--project",
            "demo-project",
            "--shot",
            "shot-001",
            "--title",
            "Opening",
            "--prompt",
            "anime boy in rain",
            "--script",
            "短句。这是一句明显更长的字幕内容。中句。",
            "--duration",
            "6",
        ],
    )
    runner.invoke(
        app,
        [
            "shot",
            "import-video",
            "--workspace",
            str(workspace),
            "--project",
            "demo-project",
            "--shot",
            "shot-001",
            "--file",
            str(source_file),
        ],
    )
    runner.invoke(
        app,
        [
            "audio",
            "generate",
            "--workspace",
            str(workspace),
            "--project",
            "demo-project",
        ],
    )

    subtitle_result = runner.invoke(
        app,
        [
            "subtitle",
            "generate",
            "--workspace",
            str(workspace),
            "--project",
            "demo-project",
        ],
    )

    subtitle_file = (
        workspace
        / "projects"
        / "demo-project"
        / "shots"
        / "shot-001"
        / "subtitles"
        / "subtitles.srt"
    )
    subtitle_text = subtitle_file.read_text(encoding="utf-8")
    ranges = _extract_srt_ranges(subtitle_text)
    durations = [_srt_time_to_ms(end) - _srt_time_to_ms(start) for start, end in ranges]

    assert subtitle_result.exit_code == 0
    assert len(ranges) == 3
    assert ranges[0][0] == "00:00:00,000"
    assert ranges[-1][1] == "00:00:06,000"
    assert durations[1] > durations[0]
    assert durations[1] > durations[2]
