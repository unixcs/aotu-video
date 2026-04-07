import asyncio
import subprocess
from pathlib import Path

from anime_pipeline.config import EdgeTTSConfig, resolve_ffmpeg_path


class EdgeTTSProvider:
    name = "edge"

    def __init__(self, config: EdgeTTSConfig) -> None:
        self._config = config

    def synthesize(self, text: str, output_path: Path) -> None:
        edge_tts = self._import_edge_tts()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        temp_output = output_path.with_suffix(".edge.mp3")

        try:
            communicate = edge_tts.Communicate(
                text,
                voice=self._config.voice,
                rate=self._config.rate,
                volume=self._config.volume,
                pitch=self._config.pitch,
            )
            asyncio.run(communicate.save(str(temp_output)))
            self._convert_to_wav(temp_output, output_path)
        finally:
            if temp_output.exists():
                temp_output.unlink()

    def _convert_to_wav(self, source_path: Path, output_path: Path) -> None:
        ffmpeg_path = resolve_ffmpeg_path()
        try:
            subprocess.run(
                [
                    str(ffmpeg_path),
                    "-y",
                    "-i",
                    str(source_path),
                    "-ac",
                    "1",
                    "-ar",
                    "16000",
                    str(output_path),
                ],
                check=True,
                capture_output=True,
            )
        except FileNotFoundError as exc:
            raise ValueError(f"FFmpeg not found: {ffmpeg_path}") from exc
        except subprocess.CalledProcessError as exc:
            stderr = exc.stderr.decode("utf-8", errors="replace").strip()
            raise ValueError(f"Edge TTS audio conversion failed: {stderr}") from exc

    def _import_edge_tts(self):
        try:
            import edge_tts
        except ModuleNotFoundError as exc:
            raise ValueError(
                "Edge TTS provider requires the 'edge-tts' package to be installed."
            ) from exc
        return edge_tts
