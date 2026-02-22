# Jockee

Automated DJ mixing app. Import a Spotify playlist, analyze every track, and play back a continuous mix with real transitions — all in the browser.

## How It Works

1. **Login** with Spotify OAuth
2. **Pick a playlist** — the backend fetches audio (yt-dlp → S3/CloudFront) and runs librosa analysis on each track (BPM, key, energy, beat grids, mix points, style classification — 15+ features)
3. **Get mix options** — server generates multiple track orderings (BPM progression, energy flow, harmonic key chaining, style clustering, compatibility optimization) with scored transitions
4. **Play** — dual-deck player executes the mix in-browser with auto-DJ, crossfader, 3-band EQ, beat sync, and waveform visualization

## Stack

| Layer | Tech |
|-------|------|
| Frontend | React 19, TypeScript, Vite, Tailwind, Jotai |
| Audio | WaveSurfer.js (waveforms), Web Audio API (EQ/routing), HTMLAudioElement (playback) |
| Backend | FastAPI, Celery + Redis, SQLAlchemy + PostgreSQL (Supabase) |
| Storage | S3 + CloudFront CDN |
| Infra | Turborepo monorepo, Bun, Docker, Render |

## Key Features

- **Audio analysis engine** — librosa/NumPy pipeline extracting BPM, key/mode, energy, danceability, valence, beat timestamps, vocal sections, mix-in/out points, and style classification per track
- **Mix generation** — 5 ordering strategies with per-transition BPM/key/energy compatibility scoring and technique selection (crossfade, smooth blend, quick cut, beatmatch)
- **Dual-deck player** — independent deck state, cosine/sine crossfader curves, `requestAnimationFrame`-driven auto-DJ, BPM-matched playback rate adjustment
- **3-band parametric EQ** — Web Audio `BiquadFilterNode` chain (320 Hz / 1 kHz / 3.2 kHz) per deck, lazily initialized
- **Waveform viz** — WaveSurfer.js with beat markers from server analysis, drag-to-seek, timeline plugin

## Dev

```bash
bun install
bun run dev        # starts all apps via Turborepo
```
