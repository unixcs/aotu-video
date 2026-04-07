from pathlib import Path
import sqlite3

import yaml

from typer.testing import CliRunner

from anime_pipeline.cli.main import app


def test_project_create_initializes_layout(tmp_path: Path) -> None:
    runner = CliRunner()
    workspace = tmp_path / "workspace"

    result = runner.invoke(
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

    project_root = workspace / "projects" / "demo-project"

    assert result.exit_code == 0
    assert project_root.exists()
    assert (project_root / "project.db").exists()
    assert (project_root / "project.yaml").exists()
    assert (project_root / "shots").is_dir()
    assert (project_root / "outputs").is_dir()
    assert (project_root / "logs").is_dir()
    assert (project_root / "previews").is_dir()


def test_project_create_persists_project_record(tmp_path: Path) -> None:
    runner = CliRunner()
    workspace = tmp_path / "workspace"

    result = runner.invoke(
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

    db_path = workspace / "projects" / "demo-project" / "project.db"
    connection = sqlite3.connect(db_path)
    try:
        row = connection.execute(
            "SELECT name, slug, ratio, target_duration FROM projects"
        ).fetchone()
    finally:
        connection.close()

    assert result.exit_code == 0
    assert row == ("Demo Project", "demo-project", "9:16", 60)


def test_project_create_reports_duplicate_slug_cleanly(tmp_path: Path) -> None:
    runner = CliRunner()
    workspace = tmp_path / "workspace"

    first_result = runner.invoke(
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
    second_result = runner.invoke(
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

    assert first_result.exit_code == 0
    assert second_result.exit_code == 1
    assert "Project 'demo-project' already exists." in second_result.stdout
    assert "IntegrityError" not in second_result.stdout


def test_project_create_sanitizes_unsafe_project_name(tmp_path: Path) -> None:
    runner = CliRunner()
    workspace = tmp_path / "workspace"

    result = runner.invoke(
        app,
        [
            "project",
            "create",
            "--workspace",
            str(workspace),
            "--name",
            "Demo/Project:01?*",
            "--ratio",
            "9:16",
            "--duration",
            "60",
        ],
    )

    expected_root = workspace / "projects" / "demo-project-01"

    assert result.exit_code == 0
    assert expected_root.exists()
    assert not (workspace / "projects" / "demo").exists()


def test_project_create_writes_parseable_yaml_metadata(tmp_path: Path) -> None:
    runner = CliRunner()
    workspace = tmp_path / "workspace"
    project_name = "Demo: Project\nLine Two"

    result = runner.invoke(
        app,
        [
            "project",
            "create",
            "--workspace",
            str(workspace),
            "--name",
            project_name,
            "--ratio",
            "9:16",
            "--duration",
            "60",
        ],
    )

    metadata_path = workspace / "projects" / "demo-project-line-two" / "project.yaml"
    metadata = yaml.safe_load(metadata_path.read_text(encoding="utf-8"))

    assert result.exit_code == 0
    assert metadata == {
        "name": project_name,
        "slug": "demo-project-line-two",
        "ratio": "9:16",
        "target_duration": 60,
    }


def test_project_create_rejects_duplicate_slug_with_user_friendly_error(
    tmp_path: Path,
) -> None:
    runner = CliRunner()
    workspace = tmp_path / "workspace"

    first_result = runner.invoke(
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
    second_result = runner.invoke(
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

    assert first_result.exit_code == 0
    assert second_result.exit_code == 1
    assert "Project 'demo-project' already exists." in second_result.stdout
    assert "IntegrityError" not in second_result.stdout


def test_project_create_generates_distinct_slugs_for_different_unicode_names(
    tmp_path: Path,
) -> None:
    runner = CliRunner()
    workspace = tmp_path / "workspace"

    first_result = runner.invoke(
        app,
        [
            "project",
            "create",
            "--workspace",
            str(workspace),
            "--name",
            "测试一",
            "--ratio",
            "9:16",
            "--duration",
            "60",
        ],
    )
    second_result = runner.invoke(
        app,
        [
            "project",
            "create",
            "--workspace",
            str(workspace),
            "--name",
            "测试二",
            "--ratio",
            "9:16",
            "--duration",
            "60",
        ],
    )

    connection = (
        sqlite3.connect(workspace / "projects" / "project" / "project.db")
        if (workspace / "projects" / "project" / "project.db").exists()
        else None
    )
    if connection is not None:
        connection.close()

    project_dirs = sorted(path.name for path in (workspace / "projects").iterdir())

    assert first_result.exit_code == 0
    assert second_result.exit_code == 0
    assert len(project_dirs) == 2
    assert project_dirs[0] != project_dirs[1]
    assert all(project_dir != "project" for project_dir in project_dirs)


def test_project_create_rejects_unsupported_ratio_before_writing_project(
    tmp_path: Path,
) -> None:
    runner = CliRunner()
    workspace = tmp_path / "workspace"

    result = runner.invoke(
        app,
        [
            "project",
            "create",
            "--workspace",
            str(workspace),
            "--name",
            "Demo Project",
            "--ratio",
            "4:3",
            "--duration",
            "60",
        ],
    )

    project_root = workspace / "projects" / "demo-project"

    assert result.exit_code == 1
    assert "Unsupported project ratio '4:3'." in result.stdout
    assert "Supported ratios: 9:16, 16:9, 1:1." in result.stdout
    assert not project_root.exists()
