import os
from pathlib import Path
from typing import NamedTuple


DEFAULT_WORKSPACE = Path("workspace")
DEFAULT_FFMPEG_PATH = Path("ffmpeg")
DEFAULT_TTS_PROVIDER = "fake"
SUPPORTED_PROJECT_RATIOS = ("9:16", "16:9", "1:1")


class CloudTTSConfig(NamedTuple):
    url: str
    api_key: str | None
    voice: str | None
    model: str | None


class EdgeTTSConfig(NamedTuple):
    voice: str
    rate: str | None
    volume: str | None
    pitch: str | None


def resolve_ffmpeg_path() -> Path:
    configured = os.getenv("FFMPEG_PATH")
    if configured:
        return Path(configured)
    return DEFAULT_FFMPEG_PATH


def resolve_tts_provider_name() -> str:
    return os.getenv("ANIME_PIPELINE_TTS_PROVIDER", DEFAULT_TTS_PROVIDER)


def validate_project_ratio(ratio: str) -> str:
    if ratio in SUPPORTED_PROJECT_RATIOS:
        return ratio
    supported = ", ".join(SUPPORTED_PROJECT_RATIOS)
    raise ValueError(
        f"Unsupported project ratio '{ratio}'. Supported ratios: {supported}."
    )


def resolve_cloud_tts_config() -> CloudTTSConfig:
    url = os.getenv("ANIME_PIPELINE_CLOUD_TTS_URL", "").strip()
    if not url:
        raise ValueError(
            "Cloud TTS provider requires ANIME_PIPELINE_CLOUD_TTS_URL to be set."
        )

    api_key = os.getenv("ANIME_PIPELINE_CLOUD_TTS_API_KEY", "").strip() or None
    voice = os.getenv("ANIME_PIPELINE_CLOUD_TTS_VOICE", "").strip() or None
    model = os.getenv("ANIME_PIPELINE_CLOUD_TTS_MODEL", "").strip() or None
    return CloudTTSConfig(url=url, api_key=api_key, voice=voice, model=model)


def resolve_edge_tts_config() -> EdgeTTSConfig:
    voice = os.getenv("ANIME_PIPELINE_EDGE_TTS_VOICE", "").strip()
    rate = os.getenv("ANIME_PIPELINE_EDGE_TTS_RATE", "").strip() or None
    volume = os.getenv("ANIME_PIPELINE_EDGE_TTS_VOLUME", "").strip() or None
    pitch = os.getenv("ANIME_PIPELINE_EDGE_TTS_PITCH", "").strip() or None
    return EdgeTTSConfig(
        voice=voice or "zh-CN-XiaoxiaoNeural",
        rate=rate,
        volume=volume,
        pitch=pitch,
    )
