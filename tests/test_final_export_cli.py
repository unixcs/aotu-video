from pathlib import Path

from typer.testing import CliRunner

from anime_pipeline.cli.main import app
from tests.media_test_utils import (
    create_test_video,
    has_audio_stream,
    has_subtitle_stream,
    require_ffmpeg,
)


def test_export_final_embeds_subtitles_into_output(tmp_path: Path, monkeypatch) -> None:
    runner = CliRunner()
    workspace = tmp_path / "workspace"
    ffmpeg_path = require_ffmpeg()
    monkeypatch.setenv("FFMPEG_PATH", ffmpeg_path)
    source_file = tmp_path / "source.mp4"
    create_test_video(ffmpeg_path, source_file, color="purple")

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
    final_result = runner.invoke(
        app,
        [
            "export",
            "final",
            "--workspace",
            str(workspace),
            "--project",
            "demo-project",
        ],
    )

    output_file = workspace / "projects" / "demo-project" / "outputs" / "final.mp4"

    assert create_result.exit_code == 0
    assert add_result.exit_code == 0
    assert import_result.exit_code == 0
    assert audio_result.exit_code == 0
    assert subtitle_result.exit_code == 0
    assert final_result.exit_code == 0
    assert output_file.exists()
    assert output_file.stat().st_size > 0
    assert has_audio_stream(ffmpeg_path, output_file)
    assert has_subtitle_stream(ffmpeg_path, output_file)


def test_export_final_fails_when_any_shot_is_missing_subtitles(
    tmp_path: Path, monkeypatch
) -> None:
    runner = CliRunner()
    workspace = tmp_path / "workspace"
    ffmpeg_path = require_ffmpeg()
    monkeypatch.setenv("FFMPEG_PATH", ffmpeg_path)

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

    for shot_no, color in [("shot-001", "purple"), ("shot-002", "orange")]:
        source_file = tmp_path / f"{shot_no}.mp4"
        create_test_video(ffmpeg_path, source_file, color=color)
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
                shot_no,
                "--title",
                shot_no,
                "--prompt",
                shot_no,
                "--script",
                shot_no,
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
                shot_no,
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

        assert add_result.exit_code == 0
        assert import_result.exit_code == 0
        assert audio_result.exit_code == 0

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
    assert subtitle_result.exit_code == 0

    missing_subtitle = (
        workspace
        / "projects"
        / "demo-project"
        / "shots"
        / "shot-002"
        / "subtitles"
        / "subtitles.srt"
    )
    missing_subtitle.unlink()

    final_result = runner.invoke(
        app,
        [
            "export",
            "final",
            "--workspace",
            str(workspace),
            "--project",
            "demo-project",
        ],
    )

    assert create_result.exit_code == 0
    assert final_result.exit_code == 1
    assert "shot-002" in final_result.stdout
    assert "subtitles.srt" in final_result.stdout


def test_export_final_fails_when_any_shot_is_missing_voice_audio(
    tmp_path: Path, monkeypatch
) -> None:
    runner = CliRunner()
    workspace = tmp_path / "workspace"
    ffmpeg_path = require_ffmpeg()
    monkeypatch.setenv("FFMPEG_PATH", ffmpeg_path)
    source_file = tmp_path / "source.mp4"
    create_test_video(ffmpeg_path, source_file, color="purple")

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
            "He walks alone in the rain.",
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
    runner.invoke(
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

    missing_audio = (
        workspace
        / "projects"
        / "demo-project"
        / "shots"
        / "shot-001"
        / "audio"
        / "voice.wav"
    )
    missing_audio.unlink()

    final_result = runner.invoke(
        app,
        [
            "export",
            "final",
            "--workspace",
            str(workspace),
            "--project",
            "demo-project",
        ],
    )

    assert final_result.exit_code == 1
    assert "shot-001" in final_result.stdout
    assert "voice.wav" in final_result.stdout


def test_export_final_ignores_draft_shots_when_completed_shots_exist(
    tmp_path: Path, monkeypatch
) -> None:
    runner = CliRunner()
    workspace = tmp_path / "workspace"
    ffmpeg_path = require_ffmpeg()
    monkeypatch.setenv("FFMPEG_PATH", ffmpeg_path)
    source_file = tmp_path / "source.mp4"
    create_test_video(ffmpeg_path, source_file, color="purple")

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
            "He walks alone in the rain.",
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
    runner.invoke(
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
            "shot-draft",
            "--title",
            "Draft",
            "--prompt",
            "Draft prompt",
            "--script",
            "Draft script",
            "--duration",
            "5",
        ],
    )

    final_result = runner.invoke(
        app,
        [
            "export",
            "final",
            "--workspace",
            str(workspace),
            "--project",
            "demo-project",
        ],
    )

    output_file = workspace / "projects" / "demo-project" / "outputs" / "final.mp4"

    assert final_result.exit_code == 0
    assert output_file.exists()


def test_export_final_reports_clear_message_when_only_draft_shots_exist(
    tmp_path: Path,
) -> None:
    runner = CliRunner()
    workspace = tmp_path / "workspace"

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
            "shot-draft",
            "--title",
            "Draft",
            "--prompt",
            "Draft prompt",
            "--script",
            "Draft script",
            "--duration",
            "5",
        ],
    )

    final_result = runner.invoke(
        app,
        [
            "export",
            "final",
            "--workspace",
            str(workspace),
            "--project",
            "demo-project",
        ],
    )

    assert create_result.exit_code == 0
    assert add_result.exit_code == 0
    assert final_result.exit_code == 1
    assert "No non-draft shots are ready for final export" in final_result.stdout


def test_export_final_reports_in_progress_non_draft_shots_clearly(
    tmp_path: Path, monkeypatch
) -> None:
    runner = CliRunner()
    workspace = tmp_path / "workspace"
    ffmpeg_path = require_ffmpeg()
    monkeypatch.setenv("FFMPEG_PATH", ffmpeg_path)
    source_file = tmp_path / "source.mp4"
    create_test_video(ffmpeg_path, source_file, color="purple")

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

    final_result = runner.invoke(
        app,
        [
            "export",
            "final",
            "--workspace",
            str(workspace),
            "--project",
            "demo-project",
        ],
    )

    assert create_result.exit_code == 0
    assert add_result.exit_code == 0
    assert import_result.exit_code == 0
    assert audio_result.exit_code == 0
    assert final_result.exit_code == 1
    assert "No subtitle-ready shots found for final export" in final_result.stdout
    assert "shot-001 (audio_ready)" in final_result.stdout
