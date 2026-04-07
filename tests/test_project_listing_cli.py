from pathlib import Path

from typer.testing import CliRunner

from anime_pipeline.cli.main import app


def test_project_list_shows_created_project(tmp_path: Path) -> None:
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
    list_result = runner.invoke(
        app,
        [
            "project",
            "list",
            "--workspace",
            str(workspace),
        ],
    )

    assert create_result.exit_code == 0
    assert list_result.exit_code == 0
    assert "demo-project" in list_result.stdout
    assert "9:16" in list_result.stdout


def test_project_show_displays_project_metadata(tmp_path: Path) -> None:
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
    show_result = runner.invoke(
        app,
        [
            "project",
            "show",
            "--workspace",
            str(workspace),
            "--project",
            "demo-project",
        ],
    )

    assert create_result.exit_code == 0
    assert show_result.exit_code == 0
    assert "name: Demo Project" in show_result.stdout
    assert "slug: demo-project" in show_result.stdout
    assert "ratio: 9:16" in show_result.stdout
    assert "target_duration: 60" in show_result.stdout


def test_project_status_summarizes_shot_pipeline_counts(tmp_path: Path) -> None:
    runner = CliRunner()
    workspace = tmp_path / "workspace"

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
            "Prompt 1",
            "--script",
            "Script 1",
            "--duration",
            "5",
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
            "shot-002",
            "--title",
            "Middle",
            "--prompt",
            "Prompt 2",
            "--script",
            "Script 2",
            "--duration",
            "5",
        ],
    )

    result = runner.invoke(
        app,
        [
            "project",
            "status",
            "--workspace",
            str(workspace),
            "--project",
            "demo-project",
        ],
    )

    assert result.exit_code == 0
    assert "project: demo-project" in result.stdout
    assert "total_shots: 2" in result.stdout
    assert "draft: 2" in result.stdout
