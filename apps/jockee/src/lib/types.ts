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
  
  // Enhanced analysis fields
  // Style analysis
  dominant_style?: string;
  style_scores?: Record<string, number>;
  style_confidence?: number;
  
  // Mix points analysis
  mix_in_point?: number;
  mix_out_point?: number;
  mixable_sections?: Array<{
    start: number;
    end: number;
    energy: number;
    beats_aligned: boolean;
  }>;
  
  // Section analysis
  intro_end?: number;
  outro_start?: number;
  intro_energy?: number;
  outro_energy?: number;
  energy_profile?: Array<{
    time: number;
    energy: number;
  }>;
  
  // Vocal analysis
  vocal_sections?: Array<{
    start: number;
    end: number;
    confidence: number;
  }>;
  instrumental_sections?: Array<{
    start: number;
    end: number;
    confidence: number;
  }>;
  
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
  technique: 'crossfade' | 'smooth_blend' | 'quick_cut' | 'beatmatch' | 'creative';
  bpm_adjustment: number;
  bpm_compatibility?: number;
  key_compatibility?: number;
  energy_compatibility?: number;
  overall_score?: number;
  metadata?: Record<string, unknown>;
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
  playlist_name?: string;
  total_tracks: number;
  analyzed_tracks: number;
  downloaded_tracks: number;
  failed_tracks: number;
  tracks?: Track[];
  mix_instructions?: MixInstructions;
  error_message?: string;
  created_at: string;
  completed_at?: string;
  progress_percentage?: number;
  updated_at?: string;
  started_at?: string;
}

// DJ Agent Types
export type DJEventType = 
  | 'track_started'
  | 'track_ended'
  | 'transition_started'
  | 'transition_ended'
  | 'mix_started'
  | 'mix_ended'
  | 'error';

export interface DJEvent {
  event_type: DJEventType;
  timestamp: number;
  data: Record<string, unknown>;
}

export type DJStatus = 'no_mix_loaded' | 'playing' | 'paused';

export interface DJState {
  status: DJStatus;
  current_position?: number;
  total_transitions?: number;
  elapsed_time?: number;
  total_duration?: number;
  progress?: number;
  current_track?: Track;
}

export interface TransitionConfig {
  track_a: Track;
  track_b: Track;
  transition: Transition;
  audio_settings?: {
    crossfade_curve?: 'linear' | 'exponential' | 'logarithmic';
    eq_matching?: boolean;
    bpm_sync?: boolean;
    beat_sync?: boolean;
  };
}

export interface AudioControllerConfig {
  backend: 'web_audio' | 'native' | 'mock';
  audio_context?: AudioContext;
  master_volume?: number;
  crossfade_quality?: 'high' | 'medium' | 'low';
}

// Enhanced API Response Types
export interface PlaylistAnalysisOptions {
  auto_fetch_missing?: boolean;
  max_tracks?: number;
  skip_analysis_if_exists?: boolean;
  download_timeout?: number;
}

export interface PlaylistAnalysisRequest {
  spotify_playlist_url: string;
  options?: PlaylistAnalysisOptions;
}

export interface JobStatusResponse {
  id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  total_tracks: number;
  analyzed_tracks: number;
  downloaded_tracks: number;
  failed_tracks: number;
  progress_percentage: number;
  error_message?: string;
  created_at: string;
  updated_at?: string;
  started_at?: string;
  completed_at?: string;
}

export interface JobResultResponse {
  id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  playlist_url: string;
  playlist_name?: string;
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