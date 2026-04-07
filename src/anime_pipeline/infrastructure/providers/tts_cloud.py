import json
from pathlib import Path
from urllib import error, request

from anime_pipeline.config import CloudTTSConfig


class CloudTTSProvider:
    name = "cloud"

    def __init__(self, config: CloudTTSConfig) -> None:
        self._config = config

    def synthesize(self, text: str, output_path: Path) -> None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"text": text}
        if self._config.voice:
            payload["voice"] = self._config.voice
        if self._config.model:
            payload["model"] = self._config.model

        headers = {"Content-Type": "application/json"}
        if self._config.api_key:
            headers["Authorization"] = f"Bearer {self._config.api_key}"

        http_request = request.Request(
            self._config.url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )

        try:
            with request.urlopen(http_request) as response:
                body = response.read()
        except error.HTTPError as exc:
            details = exc.read().decode("utf-8", errors="replace").strip()
            message = (
                f"Cloud TTS request failed with HTTP {exc.code}."
                if not details
                else f"Cloud TTS request failed with HTTP {exc.code}: {details}"
            )
            raise ValueError(message) from exc
        except error.URLError as exc:
            raise ValueError(f"Cloud TTS request failed: {exc.reason}") from exc

        if not body:
            raise ValueError("Cloud TTS response body is empty.")

        output_path.write_bytes(body)
