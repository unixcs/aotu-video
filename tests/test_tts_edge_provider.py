from __future__ import annotations

import sys
import types
import wave
from pathlib import Path

import pytest

from anime_pipeline.application.audio_service import _resolve_provider
from anime_pipeline.config import resolve_edge_tts_config
from anime_pipeline.infrastructure.providers.tts_edge import EdgeTTSProvider


def test_resolve_edge_tts_config_uses_default_voice(monkeypatch) -> None:
    monkeypatch.delenv("ANIME_PIPELINE_EDGE_TTS_VOICE", raising=False)
    monkeypatch.delenv("ANIME_PIPELINE_EDGE_TTS_RATE", raising=False)
    monkeypatch.delenv("ANIME_PIPELINE_EDGE_TTS_VOLUME", raising=False)
    monkeypatch.delenv("ANIME_PIPELINE_EDGE_TTS_PITCH", raising=False)

    config = resolve_edge_tts_config()

    assert config.voice == "zh-CN-XiaoxiaoNeural"
    assert config.rate is None
    assert config.volume is None
    assert config.pitch is None


def test_resolve_provider_supports_edge(monkeypatch) -> None:
    monkeypatch.delenv("ANIME_PIPELINE_EDGE_TTS_VOICE", raising=False)

    provider = _resolve_provider("edge")

    assert provider.name == "edge"


def test_edge_provider_synthesizes_wav_via_ffmpeg(tmp_path: Path, monkeypatch) -> None:
    captured: dict[str, object] = {}

    class FakeCommunicate:
        def __init__(
            self,
            text: str,
            *,
            voice: str,
            rate: str | None = None,
            volume: str | None = None,
            pitch: str | None = None,
        ) -> None:
            captured["text"] = text
            captured["voice"] = voice
            captured["rate"] = rate
            captured["volume"] = volume
            captured["pitch"] = pitch

        async def save(self, output_path: str) -> None:
            Path(output_path).write_bytes(b"fake-edge-mp3")

    monkeypatch.setitem(
        sys.modules,
        "edge_tts",
        types.SimpleNamespace(Communicate=FakeCommunicate),
    )

    def fake_convert(self, source_path: Path, output_path: Path) -> None:
        captured["source_suffix"] = source_path.suffix
        with wave.open(str(output_path), "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(16000)
            wav_file.writeframes(b"\x00\x00" * 160)

    monkeypatch.setattr(EdgeTTSProvider, "_convert_to_wav", fake_convert)

    provider = EdgeTTSProvider(resolve_edge_tts_config())
    output_path = tmp_path / "voice.wav"
    provider.synthesize("Edge hello", output_path)

    with wave.open(str(output_path), "rb") as wav_file:
        assert wav_file.getnchannels() == 1
        assert wav_file.getframerate() == 16000
    assert captured == {
        "text": "Edge hello",
        "voice": "zh-CN-XiaoxiaoNeural",
        "rate": None,
        "volume": None,
        "pitch": None,
        "source_suffix": ".mp3",
    }


def test_edge_provider_reports_missing_dependency(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delitem(sys.modules, "edge_tts", raising=False)

    real_import = __import__

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "edge_tts":
            raise ModuleNotFoundError("No module named 'edge_tts'")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr("builtins.__import__", fake_import)

    provider = EdgeTTSProvider(resolve_edge_tts_config())

    with pytest.raises(ValueError, match="edge-tts"):
        provider.synthesize("Edge hello", tmp_path / "voice.wav")
