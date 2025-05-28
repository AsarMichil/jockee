# Jockee - Next.js Auto-DJ Frontend

A modern web application for creating AI-powered DJ mixes from Spotify playlists with real-time audio playback and visualization.

## Features Completed ✅

### 🎵 Audio Playback Engine
- **Web Audio API Integration**: Full implementation with AudioContextManager and MixScheduler
- **Real-time Playback**: Smooth audio streaming with progress tracking
- **Crossfade Support**: AI-generated transitions with BPM adjustment
- **Volume Control**: Master volume with visual feedback
- **Seeking**: Precise timeline navigation with track-aware positioning

### 🎨 User Interface
- **Modern Design**: Clean, responsive UI with Tailwind CSS
- **Audio Visualizer**: Animated bars showing playback status
- **Track Progress**: Real-time display of current track and transitions
- **Loading States**: Progress indicators for audio loading
- **Error Handling**: User-friendly error messages and recovery

### ⌨️ User Experience
- **Keyboard Shortcuts**: 
  - `Space` - Play/Pause
  - `←/→` - Seek ±10 seconds
  - `↑/↓` - Seek ±30 seconds
- **Visual Feedback**: Transition indicators and next track preview
- **Responsive Design**: Works on desktop and mobile devices

### 🔐 Authentication & API
- **Session-based Auth**: Cookie-based authentication with Spotify OAuth
- **API Integration**: Complete REST API client with error handling
- **Real-time Updates**: Polling for analysis job status
- **Audio Streaming**: Secure audio file delivery with authentication

## Project Structure

```
apps/jockee/src/
├── app/                    # Next.js App Router pages
│   ├── login/             # Spotify OAuth login
│   ├── callback/          # OAuth callback handler
│   ├── dashboard/         # Playlist management
│   ├── analysis/          # Real-time analysis tracking
│   └── mix/[jobId]/       # Audio player interface
├── components/            # Reusable UI components
│   ├── ui/               # Base components (Button, Card, etc.)
│   ├── AudioVisualizer.tsx
│   └── TrackProgress.tsx
├── hooks/                # Custom React hooks
│   ├── useAudioPlayer.ts # Main audio playback logic
│   └── useKeyboardShortcuts.ts
├── lib/                  # Core libraries
│   ├── api/             # API client and endpoints
│   ├── audio/           # Web Audio API classes
│   ├── stores/          # Zustand state management
│   ├── types.ts         # TypeScript definitions
│   └── utils.ts         # Utility functions
└── stores/              # Global state management
    └── audioStore.ts    # Audio playback state
```

## Key Components

### AudioContextManager
Singleton class managing the Web Audio API context with proper initialization and cleanup.

### MixScheduler
Handles audio playback, crossfading, and transition scheduling with BPM adjustment support.

### useAudioPlayer Hook
Main hook integrating all audio functionality:
- Audio loading with progress tracking
- Playback controls (play/pause/seek)
- Volume and crossfader control
- Error handling and recovery

### TrackProgress Component
Real-time display showing:
- Current playing track information
- Track progress with visual bar
- Transition status and next track preview
- BPM and key information

## API Endpoints Used

- `GET /api/v1/auth/status` - Check authentication status
- `GET /api/v1/playlists` - Get user playlists
- `POST /api/v1/jobs/analyze` - Submit playlist for analysis
- `GET /api/v1/jobs/{id}/status` - Get analysis job status
- `GET /api/v1/jobs/{id}/mix` - Get mix instructions
- `GET /api/v1/tracks/{id}/audio` - Get audio stream URL

## Audio Features

### Supported Formats
- Streaming audio via authenticated endpoints
- ArrayBuffer loading for Web Audio API
- Automatic format detection and decoding

### Playback Capabilities
- Real-time position tracking
- Smooth seeking with track boundaries
- Volume control with visual feedback
- Crossfade scheduling for transitions

### Performance Optimizations
- Audio caching to prevent re-downloading
- Preloading for smooth playback
- Efficient memory management
- Background loading with progress indication

## Browser Compatibility

- **Chrome/Edge**: Full support with Web Audio API
- **Firefox**: Full support with Web Audio API
- **Safari**: Full support with Web Audio API
- **Mobile**: Responsive design with touch controls

## Development Notes

### State Management
- Zustand for audio state (playback, volume, position)
- React state for UI components and loading states
- Proper cleanup and memory management

### Error Handling
- Network error recovery
- Audio loading failure handling
- User-friendly error messages
- Graceful degradation

### Security
- Session-based authentication
- Secure audio streaming
- CORS handling for API requests
- Input validation and sanitization

## Usage

1. **Login**: Authenticate with Spotify OAuth
2. **Select Playlist**: Choose from your Spotify playlists
3. **Analyze**: Submit playlist for AI analysis
4. **Play**: Enjoy the generated mix with real-time controls

## Technical Stack

- **Framework**: Next.js 15 with App Router
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **State**: Zustand
- **Audio**: Web Audio API
- **HTTP**: Fetch API with custom client
- **Authentication**: Session-based with cookies

## Future Enhancements

- Real-time waveform visualization
- Advanced crossfade techniques
- Playlist editing and reordering
- Export functionality for mixes
- Social sharing features
- Advanced audio effects (EQ, filters)

---

**Status**: ✅ Phase 1 Complete - Ready for backend integration and testing
