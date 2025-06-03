export interface Track {
  id: string;
  spotify_id: string;
  title: string;
  artist: string;
  duration: number;
  file_source: 'local' | 'youtube' | 'unavailable';
  bpm: number;
  key: string;
  energy: number;
  
  // Beat analysis fields for beat matching
  beat_timestamps?: number[];
  beat_intervals?: number[];
  beat_confidence?: number;
  beat_confidence_scores?: number[];
  beat_regularity?: number;
  average_beat_interval?: number;
  
  // Additional audio analysis fields
  danceability?: number;
  valence?: number;
  acousticness?: number;
  instrumentalness?: number;
  liveness?: number;
  speechiness?: number;
  loudness?: number;
}

export interface Transition {
  id: string;
  position: number;
  track_a: Track;
  track_b: Track;
  transition_start: number;
  transition_duration: number;
  technique: string;
  bpm_adjustment: number;
  bpm_compatibility: number;
  key_compatibility: number;
  energy_compatibility: number;
  overall_score: number;
}

export interface MixInstructions {
  total_duration: number;
  total_tracks: number;
  transitions: Transition[];
  metadata: {
    track_count: number;
    transition_count: number;
    avg_bpm: number;
    bpm_range: { min: number; max: number };
    avg_energy: number;
    energy_range: { min: number; max: number };
    avg_compatibility: number;
    keys_used: string[];
    generation_algorithm: string;
  };
}

export interface AnalysisJob {
  id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  playlist_url: string;
  playlist_name: string;
  total_tracks: number;
  analyzed_tracks: number;
  downloaded_tracks: number;
  failed_tracks: number;
  tracks?: Track[];
  mix_instructions?: MixInstructions;
  error_message?: string;
  created_at: string;
  completed_at?: string;
}

export interface SpotifyImage {
  url: string;
  height?: number;
  width?: number;
}

export interface SpotifyOwner {
  id: string;
  display_name?: string;
  external_urls: {
    [key: string]: string;
  };
}

export interface SpotifyTracks {
  total: number;
  href: string;
}

export interface SpotifyPlaylist {
  id: string;
  name: string;
  description?: string;
  public?: boolean;
  collaborative: boolean;
  images: SpotifyImage[];
  owner: SpotifyOwner;
  tracks: SpotifyTracks;
  external_urls: {
    [key: string]: string;
  };
  snapshot_id: string;
}

export interface PlaylistsResponse {
  items: SpotifyPlaylist[];
  total: number;
  limit: number;
  offset: number;
  next?: string;
  previous?: string;
}

export interface SpotifyUser {
  id: string;
  display_name: string;
  email: string;
  images: Array<{
    url: string;
    height: number;
    width: number;
  }>;
}

export interface AudioState {
  isPlaying: boolean;
  currentTime: number;
  duration: number;
  currentTrackIndex: number;
  volume: number;
  crossfaderPosition: number;
}

export interface PlaybackState {
  currentTrack: Track | null;
  nextTrack: Track | null;
  isTransitioning: boolean;
  transitionProgress: number;
} 