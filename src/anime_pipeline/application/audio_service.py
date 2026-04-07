from pathlib import Path

from anime_pipeline.application.project_service import get_project_db_path
from anime_pipeline.config import (
    resolve_cloud_tts_config,
    resolve_edge_tts_config,
    resolve_tts_provider_name,
)
from anime_pipeline.domain.models import MediaAssetRecord
from anime_pipeline.infrastructure.db.repositories import (
    MediaAssetRepository,
    ShotRepository,
)
from anime_pipeline.infrastructure.providers.tts_base import TTSProvider
from anime_pipeline.infrastructure.providers.tts_cloud import CloudTTSProvider
from anime_pipeline.infrastructure.providers.tts_edge import EdgeTTSProvider
from anime_pipeline.infrastructure.providers.tts_fake import FakeTTSProvider


def generate_audio(
    workspace: Path, project_slug: str, provider_name: str | None = None
) -> tuple[int, str]:
    db_path = get_project_db_path(workspace, project_slug)
    shot_repository = ShotRepository(db_path)
    asset_repository = MediaAssetRepository(db_path)
    generated_count = 0
    provider = _resolve_provider(provider_name)

    for shot in shot_repository.list_by_pipeline_status("video_ready"):
        shot_root = workspace / "projects" / project_slug / "shots" / shot.shot_no
        audio_file = shot_root / "audio" / "voice.wav"
        provider.synthesize(shot.script_text, audio_file)
        asset_repository.insert(
            shot.shot_no,
            MediaAssetRecord(asset_type="voice_audio", file_path=audio_file),
        )
        shot_repository.update_pipeline_status(shot.shot_no, "audio_ready")
        generated_count += 1

    return generated_count, provider.name


def _resolve_provider(provider_name: str | None) -> TTSProvider:
    resolved_name = provider_name or resolve_tts_provider_name()
    if resolved_name == "fake":
        return FakeTTSProvider()
    if resolved_name == "cloud":
        return CloudTTSProvider(resolve_cloud_tts_config())
    if resolved_name == "edge":
        return EdgeTTSProvider(resolve_edge_tts_config())
    raise ValueError(f"Unsupported TTS provider '{resolved_name}'.")
