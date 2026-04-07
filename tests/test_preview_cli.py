from pathlib import Path

from typer.testing import CliRunner

from anime_pipeline.cli.main import app
from tests.media_test_utils import create_test_video, require_ffmpeg


def test_preview_build_generates_html_for_project_shots(
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
    preview_result = runner.invoke(
        app,
        [
            "preview",
            "build",
            "--workspace",
            str(workspace),
            "--project",
            "demo-project",
        ],
    )

    preview_file = workspace / "projects" / "demo-project" / "previews" / "index.html"

    assert create_result.exit_code == 0
    assert add_result.exit_code == 0
    assert import_result.exit_code == 0
    assert preview_result.exit_code == 0
    assert preview_file.exists()

    html = preview_file.read_text(encoding="utf-8")
    assert "Demo Project" in html
    assert "shot-001" in html
    assert "Opening" in html
    assert "video_ready" in html
    assert "normalized/clip.mp4" in html
