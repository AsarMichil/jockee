import { AudioContextManager } from "./AudioContextManager";
import { Track } from "../types";

export interface AudioTrack {
  buffer: AudioBuffer;
  track: Track;
}

export class MixScheduler {
  private audioManager: AudioContextManager;
  private currentSource: AudioBufferSourceNode | null = null;
  private nextSource: AudioBufferSourceNode | null = null;
  private currentGain: GainNode | null = null;
  private nextGain: GainNode | null = null;
  private startTime: number = 0;
  private pausedAt: number = 0;
  private isPlaying: boolean = false;
  private currentTrackId: string | null = null;
  private nextTrackId: string | null = null;
  private isInTransition: boolean = false;

  constructor() {
    this.audioManager = AudioContextManager.getInstance();
  }

  async initialize(): Promise<void> {
    const context = await this.audioManager.initialize();
    const masterGain = this.audioManager.getMasterGain();

    if (!masterGain) {
      throw new Error("Master gain node not available");
    }

    // Create gain nodes for crossfading
    this.currentGain = context.createGain();
    this.nextGain = context.createGain();

    this.currentGain.connect(masterGain);
    this.nextGain.connect(masterGain);

    // Initialize gains
    this.currentGain.gain.setValueAtTime(1, context.currentTime);
    this.nextGain.gain.setValueAtTime(0, context.currentTime);
  }

  async loadAudioBuffer(url: string): Promise<AudioBuffer> {
    const response = await fetch(url, {
      credentials: "include", // Include cookies for session authentication
      headers: {
        "Accept": "audio/*"
      }
    });

    if (!response.ok) {
      throw new Error(
        `Failed to load audio: ${response.status} ${response.statusText}`
      );
    }

    const arrayBuffer = await response.arrayBuffer();
    const context = this.audioManager.getContext();

    if (!context) {
      throw new Error("Audio context not initialized");
    }

    return await context.decodeAudioData(arrayBuffer);
  }

  async playTrack(
    audioTrack: AudioTrack,
    startOffset: number = 0,
    bpmAdjustment: number = 0
  ): Promise<void> {
    const context = this.audioManager.getContext();
    if (!context || !this.currentGain) {
      throw new Error("Audio context not initialized");
    }

    // Stop current track if playing
    this.stop();

    // Create new source
    this.currentSource = context.createBufferSource();
    this.currentSource.buffer = audioTrack.buffer;

    // Apply BPM adjustment if needed
    if (bpmAdjustment !== 0) {
      const playbackRate = 1 + bpmAdjustment / 100;
      this.currentSource.playbackRate.value = playbackRate;
      console.log(
        `Applied BPM adjustment to main track: ${bpmAdjustment}% -> playback rate: ${playbackRate}`
      );
    } else {
      this.currentSource.playbackRate.value = 1;
    }

    this.currentSource.connect(this.currentGain);

    // Set current track ID
    this.currentTrackId = audioTrack.track.id;
    this.nextTrackId = null;
    this.isInTransition = false;

    // Reset gain levels
    this.currentGain.gain.setValueAtTime(1, context.currentTime);
    if (this.nextGain) {
      this.nextGain.gain.setValueAtTime(0, context.currentTime);
    }

    // Start playback
    this.startTime = context.currentTime - startOffset;
    this.currentSource.start(0, startOffset);
    this.isPlaying = true;
    this.pausedAt = 0;
  }

  async playSecondTrack(
    audioTrack: AudioTrack,
    startOffset: number = 0,
    bpmAdjustment: number = 0
  ): Promise<void> {
    const context = this.audioManager.getContext();
    if (!context || !this.nextGain) {
      throw new Error("Audio context not initialized");
    }

    console.log(
      "playSecondTrack",
      audioTrack.track.id,
      "BPM adjustment:",
      bpmAdjustment
    );
    // Stop next source if already playing
    if (this.nextSource) {
      try {
        this.nextSource.stop();
      } catch (e: unknown) {
        console.error("Error stopping next source:", e);
        // Source might already be stopped
      }
    }

    // Create new source for next track
    this.nextSource = context.createBufferSource();
    this.nextSource.buffer = audioTrack.buffer;

    // Apply BPM adjustment BEFORE connecting and starting
    if (bpmAdjustment !== 0) {
      const playbackRate = 1 + bpmAdjustment / 100;
      this.nextSource.playbackRate.value = playbackRate;
      console.log(
        `Applied BPM adjustment: ${bpmAdjustment}% -> playback rate: ${playbackRate}`
      );
    } else {
      this.nextSource.playbackRate.value = 1;
      console.log("No BPM adjustment applied, playback rate: 1");
    }

    this.nextSource.connect(this.nextGain);

    // Set next track ID
    this.nextTrackId = audioTrack.track.id;
    this.isInTransition = true;

    // Start playback
    this.nextSource.start(0, startOffset);
    console.log(
      "Started second track with BPM adjustment:",
      bpmAdjustment,
      "playback rate:",
      this.nextSource.playbackRate.value
    );
  }

  isTrackPlaying(trackId: string): boolean {
    return this.currentTrackId === trackId || this.nextTrackId === trackId;
  }

  async startTransition(
    trackAId: string,
    trackB: AudioTrack,
    trackBStartTime: number,
    transitionDuration: number,
    technique: string,
    bpmAdjustment: number
  ): Promise<void> {
    const context = this.audioManager.getContext();
    console.log("startTransition", context, this.nextGain);
    if (!context || !this.nextGain) {
      throw new Error("Audio context not initialized");
    }

    console.log(
      "startTransition",
      trackAId,
      trackB.track.id,
      trackBStartTime,
      transitionDuration,
      technique,
      "BPM adjustment:",
      bpmAdjustment
    );
    console.log(
      "only start if not already in transition with this track",
      this.nextTrackId,
      trackB.track.id
    );
    // Only start if not already in transition with this track
    if (this.nextTrackId === trackB.track.id) {
      console.log("Already transitioning to this track, skipping");
      return;
    }
    console.log("Starting transition with BPM adjustment:", bpmAdjustment);

    // Apply BPM adjustment to the CURRENT track (track A) to match track B
    if (this.currentSource && bpmAdjustment !== 0) {
      const playbackRate = 1 + bpmAdjustment / 100;
      this.currentSource.playbackRate.value = playbackRate;
      console.log(
        `Applied BPM adjustment to current track (${trackAId}): ${bpmAdjustment}% -> playback rate: ${playbackRate}`
      );
    }

    // Start playing the second track (track B) at its natural tempo
    await this.playSecondTrack(trackB, trackBStartTime, 0); // No BPM adjustment for track B
    console.log(
      "Transition started successfully - track A adjusted, track B at natural tempo"
    );
  }

  setCrossfadeProgress(progress: number): void {
    if (!this.currentGain || !this.nextGain) return;

    const context = this.audioManager.getContext();
    if (!context) return;

    // Clamp progress between 0 and 1
    progress = Math.max(0, Math.min(1, progress));

    // Set crossfade levels
    const currentLevel = 1 - progress;
    const nextLevel = progress;

    this.currentGain.gain.setValueAtTime(currentLevel, context.currentTime);
    this.nextGain.gain.setValueAtTime(nextLevel, context.currentTime);

    // If transition is complete, swap tracks
    if (progress >= 1 && this.nextTrackId) {
      this.completeTransition();
    }
  }

  private completeTransition(): void {
    // Track B (next track) should be at natural tempo since we don't adjust it
    const nextPlaybackRate = this.nextSource?.playbackRate.value || 1;

    // Stop the old current track (track A with BPM adjustment)
    if (this.currentSource) {
      try {
        this.currentSource.stop();
      } catch (e: unknown) {
        console.error("Error stopping current source:", e);
        // Source might already be stopped
      }
    }

    // Move next track (track B) to current - it should be at natural tempo
    this.currentSource = this.nextSource;
    this.currentTrackId = this.nextTrackId;
    this.nextSource = null;
    this.nextTrackId = null;
    this.isInTransition = false;

    console.log(
      `Transition completed. Track B (now current) playback rate: ${nextPlaybackRate} (should be 1.0 for natural tempo)`
    );

    // Reset gain levels
    if (this.currentGain && this.nextGain) {
      const context = this.audioManager.getContext();
      if (context) {
        this.currentGain.gain.setValueAtTime(1, context.currentTime);
        this.nextGain.gain.setValueAtTime(0, context.currentTime);
      }
    }
  }

  pause(): void {
    if (this.isPlaying) {
      const context = this.audioManager.getContext();
      if (context) {
        this.pausedAt = context.currentTime - this.startTime;
      }
      this.stop();
    }
  }

  resume(): void {
    if (this.pausedAt > 0) {
      // Resume from paused position
      // Note: This is simplified - in a real implementation,
      // you'd need to recreate the sources and resume from the correct position
      this.pausedAt = 0;
    }
  }

  stop(): void {
    if (this.currentSource) {
      try {
        this.currentSource.stop();
      } catch (e: unknown) {
        console.error("Error stopping current source:", e);
        // Source might already be stopped
      }
      this.currentSource = null;
    }

    if (this.nextSource) {
      try {
        this.nextSource.stop();
      } catch (e: unknown) {
        console.error("Error stopping next source:", e);
        // Source might already be stopped
      }
      this.nextSource = null;
    }

    this.isPlaying = false;
  }

  getCurrentTime(): number {
    const context = this.audioManager.getContext();
    if (!context || !this.isPlaying) {
      return this.pausedAt;
    }
    const currentTime = context.currentTime - this.startTime;

    // Debug: Log time occasionally
    if (Math.floor(currentTime) % 10 === 0 && currentTime % 1 < 0.1) {
      console.log(
        "⏰ Current time:",
        currentTime,
        "Context time:",
        context.currentTime,
        "Start time:",
        this.startTime
      );
    }

    return currentTime;
  }

  setVolume(volume: number): void {
    this.audioManager.setMasterVolume(volume);
  }

  setCrossfaderPosition(position: number): void {
    if (!this.currentGain || !this.nextGain) return;

    const context = this.audioManager.getContext();
    if (!context) return;

    // Position: -1 = full current, 0 = center, 1 = full next
    const currentVolume = Math.max(0, 1 - (position + 1) / 2);
    const nextVolume = Math.max(0, (position + 1) / 2);

    this.currentGain.gain.setValueAtTime(currentVolume, context.currentTime);
    this.nextGain.gain.setValueAtTime(nextVolume, context.currentTime);
  }

  getIsPlaying(): boolean {
    return this.isPlaying;
  }

  setBpmAdjustment(trackId: string, bpmAdjustment: number): void {
    const context = this.audioManager.getContext();
    if (!context) return;

    const playbackRate = 1 + bpmAdjustment / 100;

    if (this.currentTrackId === trackId && this.currentSource) {
      this.currentSource.playbackRate.value = playbackRate;
      console.log(
        `Set BPM adjustment for current track (${trackId}): ${bpmAdjustment}% -> playback rate: ${playbackRate}`
      );
    } else if (this.nextTrackId === trackId && this.nextSource) {
      this.nextSource.playbackRate.value = playbackRate;
      console.log(
        `Set BPM adjustment for next track (${trackId}): ${bpmAdjustment}% -> playback rate: ${playbackRate}`
      );
    }
  }
}
