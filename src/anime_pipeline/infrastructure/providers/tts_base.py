from pathlib import Path
from typing import Protocol


class TTSProvider(Protocol):
    name: str

    def synthesize(self, text: str, output_path: Path) -> None: ...
