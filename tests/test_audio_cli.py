import sqlite3
import sys
import threading
import types
import wave
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from typer.testing import CliRunner

from anime_pipeline.cli.main import app
from tests.media_test_utils import create_test_video, require_ffmpeg


def test_audio_generate_creates_voice_asset_and_updates_status(
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

    audio_file = (
        workspace
        / "projects"
        / "demo-project"
        / "shots"
        / "shot-001"
        / "audio"
        / "voice.wav"
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
    assert audio_file.exists()
    assert audio_file.stat().st_size > 0
    assert shot_row == ("audio_ready",)
    assert asset_rows[-1] == ("voice_audio", str(audio_file))


def test_audio_generate_accepts_explicit_provider_override(
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
            "audio",
            "generate",
            "--workspace",
            str(workspace),
            "--project",
            "demo-project",
            "--provider",
            "fake",
        ],
    )

    assert result.exit_code == 0
    assert "Generated audio for 1 shot(s) using fake." in result.stdout


def test_audio_generate_uses_env_default_provider(tmp_path: Path, monkeypatch) -> None:
    runner = CliRunner()
    workspace = tmp_path / "workspace"
    source_file = tmp_path / "source.mp4"
    ffmpeg_path = require_ffmpeg()
    monkeypatch.setenv("FFMPEG_PATH", ffmpeg_path)
    monkeypatch.setenv("ANIME_PIPELINE_TTS_PROVIDER", "fake")
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
            "audio",
            "generate",
            "--workspace",
            str(workspace),
            "--project",
            "demo-project",
        ],
    )

    assert result.exit_code == 0
    assert "Generated audio for 1 shot(s) using fake." in result.stdout


def test_audio_generate_supports_cloud_provider(tmp_path: Path, monkeypatch) -> None:
    runner = CliRunner()
    workspace = tmp_path / "workspace"
    source_file = tmp_path / "source.mp4"
    ffmpeg_path = require_ffmpeg()
    monkeypatch.setenv("FFMPEG_PATH", ffmpeg_path)
    create_test_video(ffmpeg_path, source_file, color="red")

    response_body = b"RIFFcloud-wave-data"

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:  # noqa: N802
            self.send_response(200)
            self.send_header("Content-Type", "audio/wav")
            self.send_header("Content-Length", str(len(response_body)))
            self.end_headers()
            self.wfile.write(response_body)

        def log_message(self, format: str, *args) -> None:  # noqa: A003
            return

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    monkeypatch.setenv(
        "ANIME_PIPELINE_CLOUD_TTS_URL",
        f"http://127.0.0.1:{server.server_port}/synthesize",
    )

    try:
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
                "audio",
                "generate",
                "--workspace",
                str(workspace),
                "--project",
                "demo-project",
                "--provider",
                "cloud",
            ],
        )
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)

    audio_file = (
        workspace
        / "projects"
        / "demo-project"
        / "shots"
        / "shot-001"
        / "audio"
        / "voice.wav"
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
    assert "Generated audio for 1 shot(s) using cloud." in result.stdout
    assert audio_file.read_bytes() == response_body
    assert shot_row == ("audio_ready",)


def test_audio_generate_supports_edge_provider(tmp_path: Path, monkeypatch) -> None:
    runner = CliRunner()
    workspace = tmp_path / "workspace"
    source_file = tmp_path / "source.mp4"
    ffmpeg_path = require_ffmpeg()
    monkeypatch.setenv("FFMPEG_PATH", ffmpeg_path)
    create_test_video(ffmpeg_path, source_file, color="red")

    class FakeCommunicate:
        def __init__(self, text: str, **kwargs) -> None:
            self.text = text
            self.kwargs = kwargs

        async def save(self, output_path: str) -> None:
            Path(output_path).write_bytes(b"fake-edge-mp3")

    monkeypatch.setitem(
        sys.modules,
        "edge_tts",
        types.SimpleNamespace(Communicate=FakeCommunicate),
    )

    from anime_pipeline.infrastructure.providers.tts_edge import EdgeTTSProvider

    def fake_convert(self, source_path: Path, output_path: Path) -> None:
        with wave.open(str(output_path), "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(16000)
            wav_file.writeframes(b"\x00\x00" * 160)

    monkeypatch.setattr(EdgeTTSProvider, "_convert_to_wav", fake_convert)

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
            "audio",
            "generate",
            "--workspace",
            str(workspace),
            "--project",
            "demo-project",
            "--provider",
            "edge",
        ],
    )

    audio_file = (
        workspace
        / "projects"
        / "demo-project"
        / "shots"
        / "shot-001"
        / "audio"
        / "voice.wav"
    )
    connection = sqlite3.connect(workspace / "projects" / "demo-project" / "project.db")
    try:
        shot_row = connection.execute(
            "SELECT pipeline_status FROM shots WHERE shot_no = ?",
            ("shot-001",),
        ).fetchone()
    finally:
        connection.close()

    with wave.open(str(audio_file), "rb") as wav_file:
        channel_count = wav_file.getnchannels()
        sample_rate = wav_file.getframerate()

    assert result.exit_code == 0
    assert "Generated audio for 1 shot(s) using edge." in result.stdout
    assert shot_row == ("audio_ready",)
    assert channel_count == 1
    assert sample_rate == 16000
