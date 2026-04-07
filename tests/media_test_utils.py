from pathlib import Path
import json
import shutil
import subprocess

import pytest


WINDOWS_FFMPEG_CANDIDATES = [
    Path(r"C:\Users\fengx\AppData\Local\JianyingPro\Apps\8.9.0.13361\ffmpeg.exe"),
]


def require_ffmpeg() -> str:
    configured = shutil.which("ffmpeg")
    if configured:
        return configured

    for candidate in WINDOWS_FFMPEG_CANDIDATES:
        if candidate.exists():
            return str(candidate)

    pytest.skip("FFmpeg is required for media integration tests")


def create_test_video(
    ffmpeg_path: str,
    output_path: Path,
    *,
    color: str,
    size: str = "160x90",
    duration: str = "0.2",
    fps: str = "30",
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            ffmpeg_path,
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"color=c={color}:s={size}:d={duration}:r={fps}",
            "-pix_fmt",
            "yuv420p",
            str(output_path),
        ],
        check=True,
        capture_output=True,
    )


def create_test_wav(
    output_path: Path,
    *,
    duration_seconds: float,
    sample_rate: int = 16000,
) -> None:
    import wave

    output_path.parent.mkdir(parents=True, exist_ok=True)
    frame_count = int(duration_seconds * sample_rate)
    with wave.open(str(output_path), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(b"\x00\x00" * frame_count)


def probe_video_signature(ffmpeg_path: str, video_path: Path) -> tuple[str, str]:
    ffprobe_path = Path(ffmpeg_path).with_name("ffprobe.exe")
    if not ffprobe_path.exists():
        ffprobe_path = shutil.which("ffprobe")
    if ffprobe_path:
        result = subprocess.run(
            [
                str(ffprobe_path),
                "-v",
                "error",
                "-select_streams",
                "v:0",
                "-show_entries",
                "stream=width,height,r_frame_rate",
                "-of",
                "json",
                str(video_path),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        payload = json.loads(result.stdout)
        stream = payload["streams"][0]
        return f"{stream['width']}x{stream['height']}", stream["r_frame_rate"]

    if True:
        result = subprocess.run(
            [ffmpeg_path, "-i", str(video_path)],
            check=False,
            capture_output=True,
            text=True,
        )
        output = result.stderr

        import re

        video_line_match = re.search(
            r"Video:.*?(\d+x\d+).*?(\d+(?:\.\d+)?)\s+fps", output, re.DOTALL
        )
        if video_line_match is not None:
            return video_line_match.group(1), video_line_match.group(2)

        resolution_match = re.search(r"\b(\d{2,5}x\d{2,5})\b", output)
        fps_match = re.search(r"(\d+(?:\.\d+)?)\s+fps", output)
        if resolution_match is None or fps_match is None:
            raise AssertionError(
                f"Could not parse video signature for {video_path}: {output}"
            )
        return resolution_match.group(1), fps_match.group(1)


def has_subtitle_stream(ffmpeg_path: str, video_path: Path) -> bool:
    result = subprocess.run(
        [ffmpeg_path, "-i", str(video_path)],
        check=False,
        capture_output=True,
        text=True,
    )
    return "Subtitle:" in result.stderr


def has_audio_stream(ffmpeg_path: str, video_path: Path) -> bool:
    result = subprocess.run(
        [ffmpeg_path, "-i", str(video_path)],
        check=False,
        capture_output=True,
        text=True,
    )
    return "Audio:" in result.stderr


def extract_frame_size(ffmpeg_path: str, video_path: Path) -> tuple[int, int]:
    frame_path = video_path.with_suffix(".frame.png")
    subprocess.run(
        [
            ffmpeg_path,
            "-y",
            "-i",
            str(video_path),
            "-frames:v",
            "1",
            str(frame_path),
        ],
        check=True,
        capture_output=True,
    )

    with frame_path.open("rb") as handle:
        data = handle.read(24)
    # PNG IHDR width/height
    width = int.from_bytes(data[16:20], "big")
    height = int.from_bytes(data[20:24], "big")
    return width, height


def get_duration_seconds(ffmpeg_path: str, video_path: Path) -> float:
    ffprobe_path = Path(ffmpeg_path).with_name("ffprobe.exe")
    if not ffprobe_path.exists():
        ffprobe_path = shutil.which("ffprobe")
    if ffprobe_path:
        result = subprocess.run(
            [
                str(ffprobe_path),
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                str(video_path),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        return float(result.stdout.strip())

    result = subprocess.run(
        [ffmpeg_path, "-i", str(video_path)],
        check=False,
        capture_output=True,
        text=True,
    )
    import re

    match = re.search(r"Duration:\s+(\d+):(\d+):(\d+\.\d+)", result.stderr)
    if match is None:
        raise AssertionError(
            f"Could not parse duration for {video_path}: {result.stderr}"
        )
    hours = int(match.group(1))
    minutes = int(match.group(2))
    seconds = float(match.group(3))
    return hours * 3600 + minutes * 60 + seconds
