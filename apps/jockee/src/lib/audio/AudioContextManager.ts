export class AudioContextManager {
  private static instance: AudioContextManager;
  private context: AudioContext | null = null;
  private masterGain: GainNode | null = null;

  private constructor() {}

  static getInstance(): AudioContextManager {
    if (!AudioContextManager.instance) {
      AudioContextManager.instance = new AudioContextManager();
    }
    return AudioContextManager.instance;
  }

  async initialize(): Promise<AudioContext> {
    if (this.context && this.context.state !== "closed") {
      return this.context;
    }

    this.context = new (window.AudioContext ||
      (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext)();
    this.masterGain = this.context.createGain();
    this.masterGain.connect(this.context.destination);

    // Resume context if suspended (required by some browsers)
    if (this.context.state === "suspended") {
      await this.context.resume();
    }

    return this.context;
  }

  getContext(): AudioContext | null {
    return this.context;
  }

  getMasterGain(): GainNode | null {
    return this.masterGain;
  }

  async resume(): Promise<void> {
    if (this.context && this.context.state === "suspended") {
      await this.context.resume();
    }
  }

  suspend(): Promise<void> {
    if (this.context && this.context.state === "running") {
      return this.context.suspend();
    }
    return Promise.resolve();
  }

  close(): Promise<void> {
    if (this.context) {
      const promise = this.context.close();
      this.context = null;
      this.masterGain = null;
      return promise;
    }
    return Promise.resolve();
  }

  setMasterVolume(volume: number): void {
    if (this.masterGain) {
      this.masterGain.gain.setValueAtTime(volume, this.context!.currentTime);
    }
  }

  getCurrentTime(): number {
    return this.context?.currentTime || 0;
  }
}
