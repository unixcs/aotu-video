from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ProjectRecord:
    name: str
    slug: str
    ratio: str
    target_duration: int


@dataclass(frozen=True)
class ShotRecord:
    shot_no: str
    title: str
    prompt_text: str
    script_text: str
    target_duration: int
    pipeline_status: str = "draft"
    review_status: str = "pending"


@dataclass(frozen=True)
class MediaAssetRecord:
    asset_type: str
    file_path: Path


@dataclass(frozen=True)
class PreviewShotRecord:
    shot_no: str
    title: str
    prompt_text: str
    script_text: str
    pipeline_status: str
    normalized_video_path: str | None
