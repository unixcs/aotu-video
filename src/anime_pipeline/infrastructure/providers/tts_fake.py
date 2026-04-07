import wave
from pathlib import Path


class FakeTTSProvider:
    name = "fake"

    def synthesize(self, text: str, output_path: Path) -> None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with wave.open(str(output_path), "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(16000)
            # Very small text-length-based placeholder duration.
            frame_count = max(1600, len(text.encode("utf-8")) * 40)
            wav_file.writeframes(b"\x00\x00" * frame_count)
