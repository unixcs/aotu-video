# anime-pipeline

Local AI anime production pipeline CLI.

## Audio Providers

`audio generate` supports provider selection through `--provider` or the
`ANIME_PIPELINE_TTS_PROVIDER` environment variable.

### Fake Provider

- Provider name: `fake`
- Behavior: writes a placeholder WAV file for local development and tests

### Cloud Provider

- Provider name: `cloud`
- Request shape: `POST` JSON to a configurable HTTP endpoint
- Required env:
  - `ANIME_PIPELINE_CLOUD_TTS_URL`
- Optional env:
  - `ANIME_PIPELINE_CLOUD_TTS_API_KEY`
  - `ANIME_PIPELINE_CLOUD_TTS_VOICE`
  - `ANIME_PIPELINE_CLOUD_TTS_MODEL`

The cloud provider sends a JSON body in this shape:

```json
{
  "text": "He walks alone in the rain.",
  "voice": "narrator",
  "model": "demo-model"
}
```

If `ANIME_PIPELINE_CLOUD_TTS_API_KEY` is set, the request also includes:

```text
Authorization: Bearer <api-key>
```

The endpoint is expected to return raw audio bytes in the response body. The CLI
stores that body as `audio/voice.wav` for each `video_ready` shot.

### Edge Provider

- Provider name: `edge`
- Backend: `edge-tts`
- Output: converts generated speech into mono `16000Hz` PCM WAV at
  `audio/voice.wav`
- Optional env:
  - `ANIME_PIPELINE_EDGE_TTS_VOICE`
  - `ANIME_PIPELINE_EDGE_TTS_RATE`
  - `ANIME_PIPELINE_EDGE_TTS_VOLUME`
  - `ANIME_PIPELINE_EDGE_TTS_PITCH`

Default voice:

```text
zh-CN-XiaoxiaoNeural
```

Example:

```powershell
$env:ANIME_PIPELINE_TTS_PROVIDER = "edge"
$env:ANIME_PIPELINE_EDGE_TTS_VOICE = "zh-CN-XiaoxiaoNeural"
$env:ANIME_PIPELINE_EDGE_TTS_RATE = "+0%"
$env:ANIME_PIPELINE_EDGE_TTS_VOLUME = "+0%"
$env:ANIME_PIPELINE_EDGE_TTS_PITCH = "+0Hz"

anime-tool audio generate --project demo-project --provider edge
```
