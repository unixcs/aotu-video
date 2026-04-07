import sqlite3
from pathlib import Path

from typer.testing import CliRunner

from anime_pipeline.cli.main import app
from tests.media_test_utils import (
    create_test_video,
    extract_frame_size,
    probe_video_signature,
    require_ffmpeg,
)


def test_shot_add_creates_shot_directory_and_record(tmp_path: Path) -> None:
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

    project_root = workspace / "projects" / "demo-project"
    shot_root = project_root / "shots" / "shot-001"
    connection = sqlite3.connect(project_root / "project.db")
    try:
        row = connection.execute(
            "SELECT shot_no, title, prompt_text, script_text, target_duration, pipeline_status, review_status FROM shots"
        ).fetchone()
    finally:
        connection.close()

    assert create_result.exit_code == 0
    assert add_result.exit_code == 0
    assert shot_root.is_dir()
    assert (shot_root / "imports").is_dir()
    assert (shot_root / "generated").is_dir()
    assert (shot_root / "normalized").is_dir()
    assert (shot_root / "audio").is_dir()
    assert (shot_root / "subtitles").is_dir()
    assert (shot_root / "previews").is_dir()
    assert row == (
        "shot-001",
        "Opening",
        "anime boy in rain",
        "He walks alone in the rain.",
        5,
        "draft",
        "pending",
    )


def test_shot_list_displays_project_shots(tmp_path: Path) -> None:
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
            "anime boy in rain",
            "--script",
            "He walks alone in the rain.",
            "--duration",
            "5",
        ],
    )

    list_result = runner.invoke(
        app,
        [
            "shot",
            "list",
            "--workspace",
            str(workspace),
            "--project",
            "demo-project",
        ],
    )

    assert list_result.exit_code == 0
    assert "shot-001" in list_result.stdout
    assert "Opening" in list_result.stdout
    assert "draft" in list_result.stdout


def test_shot_add_rejects_duplicate_shot_no_with_user_friendly_error(
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
    first_add = runner.invoke(
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
    second_add = runner.invoke(
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
            "Duplicate",
            "--prompt",
            "anime boy in rain",
            "--script",
            "Duplicate shot.",
            "--duration",
            "5",
        ],
    )

    connection = sqlite3.connect(workspace / "projects" / "demo-project" / "project.db")
    try:
        count_row = connection.execute(
            "SELECT COUNT(*) FROM shots WHERE shot_no = ?",
            ("shot-001",),
        ).fetchone()
    finally:
        connection.close()

    assert create_result.exit_code == 0
    assert first_add.exit_code == 0
    assert second_add.exit_code == 1
    assert "Shot 'shot-001' already exists." in second_add.stdout
    assert "IntegrityError" not in second_add.stdout
    assert count_row == (1,)


def test_shot_add_reports_missing_project_without_creating_directories(
    tmp_path: Path,
) -> None:
    runner = CliRunner()
    workspace = tmp_path / "workspace"

    result = runner.invoke(
        app,
        [
            "shot",
            "add",
            "--workspace",
            str(workspace),
            "--project",
            "missing-project",
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

    assert result.exit_code == 1
    assert "Project 'missing-project' does not exist." in result.stdout
    assert "OperationalError" not in result.stdout
    assert not (
        workspace / "projects" / "missing-project" / "shots" / "shot-001"
    ).exists()


def test_shot_list_reports_missing_project_cleanly(tmp_path: Path) -> None:
    runner = CliRunner()
    workspace = tmp_path / "workspace"

    result = runner.invoke(
        app,
        [
            "shot",
            "list",
            "--workspace",
            str(workspace),
            "--project",
            "missing-project",
        ],
    )

    assert result.exit_code == 1
    assert "Project 'missing-project' does not exist." in result.stdout
    assert "OperationalError" not in result.stdout


def test_shot_import_video_copies_file_and_records_assets(
    tmp_path: Path, monkeypatch
) -> None:
    runner = CliRunner()
    workspace = tmp_path / "workspace"
    ffmpeg_path = require_ffmpeg()
    monkeypatch.setenv("FFMPEG_PATH", ffmpeg_path)
    source_file = tmp_path / "source.mp4"
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
            "He walks alone in the rain.",
            "--duration",
            "5",
        ],
    )

    result = runner.invoke(
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

    shot_root = workspace / "projects" / "demo-project" / "shots" / "shot-001"
    imported_file = shot_root / "imports" / "source.mp4"
    normalized_file = shot_root / "normalized" / "clip.mp4"
    connection = sqlite3.connect(workspace / "projects" / "demo-project" / "project.db")
    try:
        shot_row = connection.execute(
            "SELECT pipeline_status FROM shots WHERE shot_no = ?",
            ("shot-001",),
        ).fetchone()
        asset_rows = connection.execute(
            "SELECT asset_type, file_path FROM media_assets ORDER BY id"
        ).fetchall()
    finally:
        connection.close()

    assert result.exit_code == 0
    assert imported_file.exists()
    assert imported_file.stat().st_size > 0
    assert normalized_file.exists()
    assert normalized_file.stat().st_size > 0
    assert shot_row == ("video_ready",)
    assert asset_rows == [
        ("imported_video", str(imported_file)),
        ("normalized_video", str(normalized_file)),
    ]


def test_shot_scan_imports_imports_pending_files(tmp_path: Path, monkeypatch) -> None:
    runner = CliRunner()
    workspace = tmp_path / "workspace"
    ffmpeg_path = require_ffmpeg()
    monkeypatch.setenv("FFMPEG_PATH", ffmpeg_path)

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

    import_drop = (
        workspace
        / "projects"
        / "demo-project"
        / "shots"
        / "shot-001"
        / "imports"
        / "dropped.mp4"
    )
    create_test_video(ffmpeg_path, import_drop, color="blue")

    result = runner.invoke(
        app,
        [
            "shot",
            "scan-imports",
            "--workspace",
            str(workspace),
            "--project",
            "demo-project",
        ],
    )

    normalized_file = (
        workspace
        / "projects"
        / "demo-project"
        / "shots"
        / "shot-001"
        / "normalized"
        / "clip.mp4"
    )
    connection = sqlite3.connect(workspace / "projects" / "demo-project" / "project.db")
    try:
        shot_row = connection.execute(
            "SELECT pipeline_status FROM shots WHERE shot_no = ?",
            ("shot-001",),
        ).fetchone()
    finally:
        connection.close()

    assert result.exit_code == 0
    assert "Imported 1 shot(s)." in result.stdout
    assert normalized_file.exists()
    assert normalized_file.stat().st_size > 0
    assert shot_row == ("video_ready",)


def test_shot_scan_imports_supports_mov_files(tmp_path: Path, monkeypatch) -> None:
    runner = CliRunner()
    workspace = tmp_path / "workspace"
    ffmpeg_path = require_ffmpeg()
    monkeypatch.setenv("FFMPEG_PATH", ffmpeg_path)

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

    import_drop = (
        workspace
        / "projects"
        / "demo-project"
        / "shots"
        / "shot-001"
        / "imports"
        / "dropped.mov"
    )
    create_test_video(ffmpeg_path, import_drop, color="green")

    result = runner.invoke(
        app,
        [
            "shot",
            "scan-imports",
            "--workspace",
            str(workspace),
            "--project",
            "demo-project",
        ],
    )

    normalized_file = (
        workspace
        / "projects"
        / "demo-project"
        / "shots"
        / "shot-001"
        / "normalized"
        / "clip.mp4"
    )

    assert result.exit_code == 0
    assert "Imported 1 shot(s)." in result.stdout
    assert normalized_file.exists()
    assert normalized_file.stat().st_size > 0


def test_shot_scan_imports_skips_shots_without_imports_directory(
    tmp_path: Path, monkeypatch
) -> None:
    runner = CliRunner()
    workspace = tmp_path / "workspace"
    ffmpeg_path = require_ffmpeg()
    monkeypatch.setenv("FFMPEG_PATH", ffmpeg_path)

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

    incomplete_shot_root = (
        workspace / "projects" / "demo-project" / "shots" / "shot-incomplete"
    )
    incomplete_shot_root.mkdir(parents=True, exist_ok=True)

    import_drop = (
        workspace
        / "projects"
        / "demo-project"
        / "shots"
        / "shot-001"
        / "imports"
        / "dropped.mp4"
    )
    create_test_video(ffmpeg_path, import_drop, color="green")

    result = runner.invoke(
        app,
        [
            "shot",
            "scan-imports",
            "--workspace",
            str(workspace),
            "--project",
            "demo-project",
        ],
    )

    normalized_file = (
        workspace
        / "projects"
        / "demo-project"
        / "shots"
        / "shot-001"
        / "normalized"
        / "clip.mp4"
    )

    assert result.exit_code == 0
    assert "Imported 1 shot(s)." in result.stdout
    assert normalized_file.exists()


def test_shot_import_video_rejects_orphan_directory_without_db_record(
    tmp_path: Path,
) -> None:
    runner = CliRunner()
    workspace = tmp_path / "workspace"
    source_file = tmp_path / "source.mp4"
    source_file.write_bytes(b"fake-video-content")

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

    orphan_root = workspace / "projects" / "demo-project" / "shots" / "shot-orphan"
    for path in [
        orphan_root,
        orphan_root / "imports",
        orphan_root / "generated",
        orphan_root / "normalized",
        orphan_root / "audio",
        orphan_root / "subtitles",
        orphan_root / "previews",
    ]:
        path.mkdir(parents=True, exist_ok=True)

    result = runner.invoke(
        app,
        [
            "shot",
            "import-video",
            "--workspace",
            str(workspace),
            "--project",
            "demo-project",
            "--shot",
            "shot-orphan",
            "--file",
            str(source_file),
        ],
    )

    connection = sqlite3.connect(workspace / "projects" / "demo-project" / "project.db")
    try:
        asset_count = connection.execute("SELECT COUNT(*) FROM media_assets").fetchone()
        shot_count = connection.execute(
            "SELECT COUNT(*) FROM shots WHERE shot_no = ?",
            ("shot-orphan",),
        ).fetchone()
    finally:
        connection.close()

    assert result.exit_code == 1
    assert (
        "Shot 'shot-orphan' does not exist in project 'demo-project'." in result.stdout
    )
    assert asset_count == (0,)
    assert shot_count == (0,)


def test_shot_scan_imports_rejects_orphan_directory_without_writing_assets(
    tmp_path: Path,
) -> None:
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

    orphan_root = workspace / "projects" / "demo-project" / "shots" / "shot-orphan"
    for path in [
        orphan_root,
        orphan_root / "imports",
        orphan_root / "generated",
        orphan_root / "normalized",
        orphan_root / "audio",
        orphan_root / "subtitles",
        orphan_root / "previews",
    ]:
        path.mkdir(parents=True, exist_ok=True)

    drop_file = orphan_root / "imports" / "drop.mp4"
    drop_file.write_bytes(b"orphan-video")

    result = runner.invoke(
        app,
        [
            "shot",
            "scan-imports",
            "--workspace",
            str(workspace),
            "--project",
            "demo-project",
        ],
    )

    connection = sqlite3.connect(workspace / "projects" / "demo-project" / "project.db")
    try:
        asset_count = connection.execute(
            "SELECT COUNT(*) FROM media_assets WHERE shot_no = ?",
            ("shot-orphan",),
        ).fetchone()
    finally:
        connection.close()

    assert result.exit_code == 1
    assert "Shot 'shot-orphan' does not exist." in result.stdout
    assert asset_count == (0,)


def test_shot_import_video_normalizes_heterogeneous_inputs_to_same_signature(
    tmp_path: Path, monkeypatch
) -> None:
    runner = CliRunner()
    workspace = tmp_path / "workspace"
    ffmpeg_path = require_ffmpeg()
    monkeypatch.setenv("FFMPEG_PATH", ffmpeg_path)

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

    source_specs = [
        ("shot-001", "red", "160x90", "30"),
        ("shot-002", "blue", "200x120", "24"),
    ]

    normalized_signatures = []
    for shot_no, color, size, fps in source_specs:
        source_file = tmp_path / f"{shot_no}.mp4"
        create_test_video(ffmpeg_path, source_file, color=color, size=size, fps=fps)
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
        assert import_result.exit_code == 0

        normalized_file = (
            workspace
            / "projects"
            / "demo-project"
            / "shots"
            / shot_no
            / "normalized"
            / "clip.mp4"
        )
        normalized_signatures.append(
            probe_video_signature(ffmpeg_path, normalized_file)
        )
        assert extract_frame_size(ffmpeg_path, normalized_file) == (720, 1280)

    assert normalized_signatures[0] == normalized_signatures[1]


def test_shot_show_displays_status_and_asset_paths(tmp_path: Path, monkeypatch) -> None:
    runner = CliRunner()
    workspace = tmp_path / "workspace"
    ffmpeg_path = require_ffmpeg()
    monkeypatch.setenv("FFMPEG_PATH", ffmpeg_path)
    source_file = tmp_path / "source.mp4"
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

    show_result = runner.invoke(
        app,
        [
            "shot",
            "show",
            "--workspace",
            str(workspace),
            "--project",
            "demo-project",
            "--shot",
            "shot-001",
        ],
    )

    assert show_result.exit_code == 0
    assert "shot_no: shot-001" in show_result.stdout
    assert "title: Opening" in show_result.stdout
    assert "pipeline_status: video_ready" in show_result.stdout
    assert "normalized_video:" in show_result.stdout
    assert "clip.mp4" in show_result.stdout


def test_shot_status_displays_asset_presence_flags(tmp_path: Path, monkeypatch) -> None:
    runner = CliRunner()
    workspace = tmp_path / "workspace"
    ffmpeg_path = require_ffmpeg()
    monkeypatch.setenv("FFMPEG_PATH", ffmpeg_path)
    source_file = tmp_path / "source.mp4"
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

    result = runner.invoke(
        app,
        [
            "shot",
            "status",
            "--workspace",
            str(workspace),
            "--project",
            "demo-project",
            "--shot",
            "shot-001",
        ],
    )

    assert result.exit_code == 0
    assert "shot_no: shot-001" in result.stdout
    assert "pipeline_status: video_ready" in result.stdout
    assert "has_normalized_video: true" in result.stdout
    assert "has_audio: false" in result.stdout
    assert "has_subtitles: false" in result.stdout
