# Findings

## Candidate Themes
- Remotion-based editors and generators
- Python/FFmpeg automation pipelines for Shorts
- Local/self-hosted AI video orchestration projects
- CapCut/Jianying automation as editing/export backends

## Early Candidates
- designcombo/react-video-editor
- trykimu/videoeditor
- gyoridavid/short-video-maker
- 45ck/content-machine
- FolhaSP/mosaico
- Auto-Vio/autovio
- digitalsamba/claude-code-video-toolkit
- Agents365-ai/video-podcast-maker
- ChaituRajSagar/gemini-youtube-automation
- mikeoller82/VideoGraphAI
- qingpingwang/jianying-protocol-service
- Hommy-master/capcut-mate

## Reviewed Repo Notes
- `designcombo/react-video-editor`: Next.js/TypeScript Remotion editor; 1.5k stars, 371 forks, 33 commits, 22 issues. Strong timeline/multitrack/export UI foundation but little built-in AI pipeline logic.
- `trykimu/videoeditor`: TypeScript + Python + Docker + Postgres + FastAPI + Remotion; 1.3k stars, 144 forks, 465 commits, 33 issues. Strongest open editing foundation with AI assistant hooks and backend services.
- `gyoridavid/short-video-maker`: TypeScript Remotion REST/MCP server; 1.1k stars, 353 forks, 122 commits. Practical short-video generator with Kokoro TTS, Whisper captions, FFmpeg, Docker; limited asset sourcing and no real storyboard editor.
- `45ck/content-machine`: TypeScript CLI with npm releases; 358 commits, 3 releases, tests/docs, but only 7 stars. Strong modular pipeline (`script -> audio -> visuals -> render`) and good architecture despite low adoption.
- `FolhaSP/mosaico`: Python package on PyPI; 101 commits, 26 releases. Solid library-level composition primitives, assets, timeline, TTS hooks, script generation; less turnkey as a product.
- `Auto-Vio/autovio`: React/Express/Mongo self-hosted orchestrator; 36 commits, initial release, MCP-ready, FFmpeg export. Good end-to-end concept including scenario and editor, but still early and noncommercial license reduces fit.
- `digitalsamba/claude-code-video-toolkit`: Python + TypeScript toolkit; 696 stars, 102 forks, 143 commits, 21 releases. Excellent reusable project lifecycle, templates, transitions, voice/music/image/video tooling; more toolkit than app.
- `Agents365-ai/video-podcast-maker`: TypeScript + Python + Remotion; 366 stars, 48 forks, 258 commits, 9 releases. Strong TTS/subtitle/render pipeline for long-form podcast/explainer videos; narrower format bias.
- `ChaituRajSagar/gemini-youtube-automation`: Python moviepy/GitHub Actions pipeline; 249 stars, 116 forks, 245 commits. Practical automation repo but README and architecture depth look relatively light compared with stronger candidates.
- `mikeoller82/VideoGraphAI`: Streamlit Python app; 54 stars, 51 commits, beta. Includes research, storyboard/media, F5-TTS, subtitles, FFmpeg. Interesting donor for graph-agent orchestration, but not highly mature.
- `qingpingwang/jianying-protocol-service`: FastAPI programmatic Jianying/CapCut draft API; 28 stars, 7 commits. Useful backend module for draft/project generation and track/effect APIs; too narrow and early as main foundation.
- `Hommy-master/capcut-mate`: FastAPI CapCut/Jianying automation server; 666 stars, 128 forks, 423 commits, 72 releases. Mature automation backend with draft ops, captions, effects, keyframes, rendering, workflow integrations; strongest module donor if CapCut/Jianying is acceptable dependency.
