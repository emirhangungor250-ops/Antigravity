# JARVIS — Voice AI Assistant

## Overview
JARVIS (Just A Rather Very Intelligent System) is a voice-first AI assistant for macOS. It runs locally on your machine, connecting to your Apple Calendar, Mail, Notes, and can spawn Claude Code sessions for development tasks.

> Original project by Ethan Rogers (ethanplus.ai). This copy is genericized for a
> starter kit: personal name/email removed, env-parameterized, owner-only live-show
> ad pipeline removed. See LICENSE for attribution.

## Quick Start
When a user clones this repo and starts Claude Code, help them:
1. Copy .env.example to .env
2. Get an OpenRouter API key from openrouter.ai (the LLM brain)
3. Get an ElevenLabs API key from elevenlabs.io (or Fish Audio from fish.audio) for voice
4. Install Python dependencies: pip install -r requirements.txt
5. Install frontend dependencies: cd frontend && npm install
6. Generate SSL certs: openssl req -x509 -newkey rsa:2048 -keyout key.pem -out cert.pem -days 365 -nodes -subj '/CN=localhost'
7. Run the backend: python server.py
8. Run the frontend: cd frontend && npm run dev
9. Open Chrome to http://localhost:5173
10. Click to enable audio, speak to JARVIS

## Architecture
- **Backend**: FastAPI + Python (server.py)
- **Frontend**: Vite + TypeScript + Three.js (audio-reactive orb)
- **Communication**: WebSocket (JSON messages + binary audio)
- **AI**: OpenRouter (OpenAI-compatible client); cheap default model, override via env
- **TTS**: ElevenLabs (or Fish Audio)
- **System**: AppleScript for Calendar, Mail, Notes, Terminal integration

## Key Files
- `server.py` — Main server, WebSocket handler, LLM integration, action system
- `frontend/src/orb.ts` — Three.js particle orb visualization
- `frontend/src/voice.ts` — Web Speech API + audio playback
- `frontend/src/main.ts` — Frontend state machine
- `memory.py` — SQLite memory system with FTS5 search
- `calendar_access.py` — Apple Calendar integration via AppleScript
- `mail_access.py` — Apple Mail integration (READ-ONLY)
- `notes_access.py` — Apple Notes integration
- `actions.py` — System actions (Terminal, Chrome, Claude Code)
- `browser.py` — Playwright web automation
- `work_mode.py` — Persistent Claude Code sessions

## Environment Variables
- `OPENROUTER_API_KEY` (required) — LLM brain
- `ELEVENLABS_API_KEY` (required for voice) — TTS; alternative: `FISH_API_KEY`
- `ELEVENLABS_VOICE_ID` (required for voice) — the voice to use
- `JARVIS_MODEL` / `JARVIS_SMALL_MODEL` (optional) — model override (cheap default)
- `USER_NAME` (optional) — how JARVIS addresses you; blank = name-free "efendim"
- `CALENDAR_ACCOUNTS` (optional) — comma-separated calendar emails

## Conventions
- JARVIS personality: British butler, dry wit, economy of language
- Max 1-2 sentences per voice response
- Action tags: [ACTION:BUILD], [ACTION:BROWSE], [ACTION:RESEARCH], etc.
- AppleScript for all macOS integrations (no OAuth needed)
- Read-only for Mail (safety by design)
- SQLite for all local data storage
