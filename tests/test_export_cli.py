from pathlib import Path
import subprocess

from typer.testing import CliRunner

from anime_pipeline.cli.main import app
from tests.media_test_utils import (
    create_test_video,
    get_duration_seconds,
    require_ffmpeg,
)


def test_export_rough_cut_concatenates_ready_shots(tmp_path: Path, monkeypatch) -> None:
    runner = CliRunner()
    workspace = tmp_path / "workspace"
    ffmpeg_path = require_ffmpeg()
    monkeypatch.setenv("FFMPEG_PATH", ffmpeg_path)

    for shot_no, title, color in [
        ("shot-001", "Opening", "red"),
        ("shot-002", "Ending", "blue"),
    ]:
        source_file = tmp_path / f"{shot_no}.mp4"
        build_source = (
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
            if shot_no == "shot-001"
            else None
        )

        if build_source is not None:
            assert build_source.exit_code == 0

        ffmpeg_generate = runner.invoke(
            app,
            [
                "project",
                "list",
                "--workspace",
                str(workspace),
            ],
        )
        assert ffmpeg_generate.exit_code == 0

        create_test_video(
            ffmpeg_path,
            source_file,
            color=color,
            size="160x90" if shot_no == "shot-001" else "200x120",
            fps="30" if shot_no == "shot-001" else "24",
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
                shot_no,
                "--title",
                title,
                "--prompt",
                f"{title} prompt",
                "--script",
                f"{title} script",
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

        assert add_result.exit_code == 0
        assert import_result.exit_code == 0

    export_result = runner.invoke(
        app,
        [
            "export",
            "rough-cut",
            "--workspace",
            str(workspace),
            "--project",
            "demo-project",
        ],
    )

    output_file = workspace / "projects" / "demo-project" / "outputs" / "rough_cut.mp4"

    assert export_result.exit_code == 0
    assert output_file.exists()
    assert output_file.stat().st_size > 0
    assert get_duration_seconds(ffmpeg_path, output_file) >= 0.35


def test_export_rough_cut_reports_missing_ffmpeg_cleanly(
    tmp_path: Path, monkeypatch
) -> None:
    runner = CliRunner()
    workspace = tmp_path / "workspace"
    source_file = tmp_path / "source.mp4"
    ffmpeg_path = require_ffmpeg()
    create_test_video(ffmpeg_path, source_file, color="red")
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
            "Opening prompt",
            "--script",
            "Opening script",
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
    monkeypatch.setenv("FFMPEG_PATH", str(tmp_path / "missing-ffmpeg.exe"))

    export_result = runner.invoke(
        app,
        [
            "export",
            "rough-cut",
            "--workspace",
            str(workspace),
            "--project",
            "demo-project",
        ],
    )

    assert create_result.exit_code == 0
    assert add_result.exit_code == 0
    assert import_result.exit_code == 0
    assert export_result.exit_code == 1
    assert "FFmpeg not found" in export_result.stdout


def test_export_rough_cut_uses_env_ffmpeg_path_and_handles_apostrophe_paths(
    tmp_path: Path, monkeypatch
) -> None:
    base_root = tmp_path / "O'Neil"
    workspace = base_root / "workspace"
    workspace.parent.mkdir(parents=True, exist_ok=True)

    runner = CliRunner()
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
    assert create_result.exit_code == 0

    for shot_no, color in [("shot-001", "red"), ("shot-002", "blue")]:
        source_file = base_root / f"{shot_no}.mp4"
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
        assert add_result.exit_code == 0
        assert import_result.exit_code == 0

    export_result = runner.invoke(
        app,
        [
            "export",
            "rough-cut",
            "--workspace",
            str(workspace),
            "--project",
            "demo-project",
        ],
    )

    output_file = workspace / "projects" / "demo-project" / "outputs" / "rough_cut.mp4"

    assert export_result.exit_code == 0
    assert output_file.exists()
    assert output_file.stat().st_size > 0


def test_export_rough_cut_still_accepts_audio_ready_shots(
    tmp_path: Path, monkeypatch
) -> None:
    runner = CliRunner()
    workspace = tmp_path / "workspace"
    ffmpeg_path = require_ffmpeg()
    monkeypatch.setenv("FFMPEG_PATH", ffmpeg_path)
    source_file = tmp_path / "source.mp4"

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
    create_test_video(ffmpeg_path, source_file, color="green")
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
            "Opening prompt",
            "--script",
            "Opening script",
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
    export_result = runner.invoke(
        app,
        [
            "export",
            "rough-cut",
            "--workspace",
            str(workspace),
            "--project",
            "demo-project",
        ],
    )

    output_file = workspace / "projects" / "demo-project" / "outputs" / "rough_cut.mp4"

    assert create_result.exit_code == 0
    assert add_result.exit_code == 0
    assert import_result.exit_code == 0
    assert audio_result.exit_code == 0
    assert export_result.exit_code == 0
    assert output_file.exists()


def test_export_rough_cut_handles_relative_workspace_paths(
    tmp_path: Path, monkeypatch
) -> None:
    runner = CliRunner()
    workspace_name = "workspace"
    ffmpeg_path = require_ffmpeg()
    monkeypatch.setenv("FFMPEG_PATH", ffmpeg_path)
    source_file = tmp_path / "source.mp4"
    create_test_video(ffmpeg_path, source_file, color="yellow")
    monkeypatch.chdir(tmp_path)

    create_result = runner.invoke(
        app,
        [
            "project",
            "create",
            "--workspace",
            workspace_name,
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
            workspace_name,
            "--project",
            "demo-project",
            "--shot",
            "shot-001",
            "--title",
            "Opening",
            "--prompt",
            "Opening prompt",
            "--script",
            "Opening script",
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
            workspace_name,
            "--project",
            "demo-project",
            "--shot",
            "shot-001",
            "--file",
            str(source_file),
        ],
    )
    export_result = runner.invoke(
        app,
        [
            "export",
            "rough-cut",
            "--workspace",
            workspace_name,
            "--project",
            "demo-project",
        ],
    )

    output_file = (
        tmp_path
        / workspace_name
        / "projects"
        / "demo-project"
        / "outputs"
        / "rough_cut.mp4"
    )

    assert create_result.exit_code == 0
    assert add_result.exit_code == 0
    assert import_result.exit_code == 0
    assert export_result.exit_code == 0
    assert output_file.exists()
