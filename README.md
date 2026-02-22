# Auto-DJ

Full-stack automated DJ mixing platform. Import a Spotify playlist → analyze every track's audio features → generate a continuous mix with real transitions → play it back in a dual-deck browser player.

## Architecture

```
apps/
├── jockee/    React 19 dual-deck DJ player (Vite + TypeScript)
├── landing/   Marketing landing page (Vite + React)
└── server/    FastAPI backend + Celery workers (Python)
```

**Monorepo** managed with Turborepo and Bun workspaces.

## How It Works

1. **Authenticate** via Spotify OAuth
2. **Select a playlist** — backend fetches tracks from Spotify API
3. **Download & analyze** — Celery workers download audio (yt-dlp → S3 + CloudFront) and run librosa analysis per track: BPM, musical key/mode, energy, danceability, valence, beat grids, vocal sections, mix-in/out points, style classification (15+ features)
4. **Generate mix** — server produces multiple track orderings (BPM progression, energy flow, harmonic key chaining, style clustering, compatibility optimization) with per-transition compatibility scores and technique selection
5. **Play** — browser dual-deck player executes the mix with auto-DJ, crossfader, 3-band EQ, beat sync, and waveform visualization

## Tech Stack

| | |
|---|---|
| **Frontend** | React 19, TypeScript, Vite, Tailwind CSS, Jotai (atomic state) |
| **Audio** | WaveSurfer.js (waveforms), Web Audio API (EQ/routing), HTMLAudioElement (playback) |
| **Backend** | FastAPI, Celery + Redis (task queue), SQLAlchemy + PostgreSQL (Supabase) |
| **Analysis** | librosa, NumPy, SciPy, yt-dlp, FFmpeg |
| **Storage** | AWS S3 + CloudFront CDN |
| **Auth** | Spotify OAuth via spotipy, JWT (python-jose) |
| **Infra** | Docker, Render, Turborepo, Bun |

## Getting Started

```bash
# install dependencies
bun install

# start all apps (frontend + landing + server)
bun run dev

# or run individually
cd apps/server && bun run dev:api      # FastAPI on :8000
cd apps/server && bun run dev:worker   # Celery worker
cd apps/jockee && bun run dev          # React app on :5173
cd apps/landing && bun run dev         # Landing page on :5174
```

### Prerequisites

- Bun
- Python 3.10+
- Redis
- FFmpeg
- PostgreSQL (or Supabase)
- Spotify Developer credentials
- AWS credentials (S3 bucket + CloudFront distribution)

### Environment Variables

Server requires (see `apps/server/app/core/config.py`):

```
DATABASE_URL, REDIS_URL, SECRET_KEY,
SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, SPOTIFY_REDIRECT_URI,
AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, S3_BUCKET_NAME, CLOUDFRONT_DOMAIN,
CELERY_BROKER_URL, CELERY_RESULT_BACKEND
```

## Project Highlights

- **Audio analysis engine** — 1,600-line librosa/NumPy pipeline extracting BPM, key via chroma features, energy, danceability, valence, beat timestamps with confidence scores, vocal/instrumental section detection, optimal mix points, and style classification
- **Mix generation** — 5 ordering strategies with greedy harmonic/BPM/energy compatibility scoring; transition technique selection (crossfade, smooth blend, quick cut, beatmatch)
- **Dual-deck player** — independent deck state, cosine/sine crossfader volume curves, `requestAnimationFrame`-driven auto-DJ engine with strategy pattern for transitions, BPM-matched playback rate adjustment
- **3-band parametric EQ** — Web Audio `BiquadFilterNode` chain (320 Hz / 1 kHz / 3.2 kHz) per deck, lazily initialized via `AudioContext`
- **Waveform visualization** — WaveSurfer.js rendering beat markers from server analysis, drag-to-seek, timeline plugin
- **Cloud audio pipeline** — yt-dlp download → FFmpeg loudness normalization → S3 upload → CloudFront delivery with 1-year cache headers
