from __future__ import annotations

import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

from anime_pipeline.application.audio_service import _resolve_provider


def test_resolve_provider_rejects_cloud_without_required_config(monkeypatch) -> None:
    monkeypatch.delenv("ANIME_PIPELINE_CLOUD_TTS_URL", raising=False)

    with pytest.raises(ValueError, match="ANIME_PIPELINE_CLOUD_TTS_URL"):
        _resolve_provider("cloud")


def test_cloud_provider_synthesizes_audio_from_http_response(
    tmp_path: Path, monkeypatch
) -> None:
    requests: list[dict[str, str]] = []
    response_body = b"RIFFtest-wave-data"

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:  # noqa: N802
            content_length = int(self.headers["Content-Length"])
            payload = self.rfile.read(content_length).decode("utf-8")
            requests.append(
                {
                    "authorization": self.headers.get("Authorization", ""),
                    "content_type": self.headers.get("Content-Type", ""),
                    "payload": payload,
                }
            )
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
    monkeypatch.setenv("ANIME_PIPELINE_CLOUD_TTS_API_KEY", "secret-key")
    monkeypatch.setenv("ANIME_PIPELINE_CLOUD_TTS_VOICE", "narrator")
    monkeypatch.setenv("ANIME_PIPELINE_CLOUD_TTS_MODEL", "demo-model")

    try:
        provider = _resolve_provider("cloud")
        output_path = tmp_path / "voice.wav"

        provider.synthesize("Hello cloud voice", output_path)
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)

    assert output_path.read_bytes() == response_body
    assert requests == [
        {
            "authorization": "Bearer secret-key",
            "content_type": "application/json",
            "payload": (
                '{"text": "Hello cloud voice", '
                '"voice": "narrator", '
                '"model": "demo-model"}'
            ),
        }
    ]
