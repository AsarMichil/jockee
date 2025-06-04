import { setDeckWavesurfer, store } from "@/lib/audio/Audio";
import { useAudioStore } from "@/lib/audio/AudioStoreProvider";
import WavesurferPlayer from "@wavesurfer/react";
import { useState } from "react";
import type WaveSurfer from "wavesurfer.js";

export default function WaveformVisualizer({
  deck,
  trackTitle,
  loaded
}: {
  deck: "A" | "B";
  trackTitle: string;
  loaded: boolean;
}) {
  console.log("WaveformVisualizer", deck);
  const [zoom, setZoom] = useState(100);
  const [wavesurfer, setWavesurfer] = useState<WaveSurfer | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const onReady = (ws: WaveSurfer) => {
    console.log("onReady", ws);
    setWavesurfer(ws);
    setIsPlaying(false);
    setDeckWavesurfer(deck === "A" ? "deckA" : "deckB", ws);
  };

  const audioElement = useAudioStore((state) =>
    deck === "A" ? state.deckAAudioElement : state.deckBAudioElement
  );
  const onPlayPause = () => {
    wavesurfer?.playPause();
  };

  const handleZoomChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newZoom = parseInt(e.target.value);
    console.log("handleZoomChange", newZoom);
    setZoom(newZoom);

    // Apply zoom if wavesurfer instance is available
    if (wavesurfer) {
      wavesurfer.zoom(newZoom);
    }
  };

  if (!loaded) {
    return <div>Loading...</div>;
  }

  return (
    <div>
      <WavesurferPlayer
        onFinish={handleEnded(deck === "A" ? "deckA" : "deckB")}
        onReady={onReady}
        height={100}
        waveColor="violet"
        media={audioElement}
        minPxPerSec={zoom}
        dragToSeek={true}
        onPlay={() => setIsPlaying(true)}
        onPause={() => setIsPlaying(false)}
      />

      <div className="flex items-center justify-between mt-2 mb-2">
        <label className="flex items-center gap-2 text-sm">
          Zoom:
          <input
            type="range"
            min="10"
            max="1000"
            value={zoom}
            onChange={handleZoomChange}
            className="w-24"
          />
          <span className="text-xs text-gray-500">{zoom}px/sec</span>
        </label>
      </div>

      <div className="flex items-center justify-between mt-2">
        <span className="text-sm text-gray-600 truncate">{trackTitle}</span>
        <button
          onClick={onPlayPause}
          className="px-3 py-1 bg-blue-500 text-white rounded hover:bg-blue-600"
        >
          {isPlaying ? "Pause" : "Play"}
        </button>
      </div>
    </div>
  );
}

// Add ended event listener for autoplay functionality
const handleEnded = (deck: "deckA" | "deckB") => {
  return () => {
    console.log("onFinish");
    const state = store.getState();
    if (state.autoplay) {
      store.getState().autoplayNextTrack(deck);
    } else {
      // Clear the track and reset the deck state
      store.setState({
        ...state,
        [deck]: {
          ...state[deck],
          isLoading: false,
          isLoaded: false,
          track: null
        }
      });
    }
  };
};

const handlePlaying = (deck: "deckA" | "deckB") => {
  return () => {
    console.log(`Track started on ${deck}`);
    const state = store.getState();
    store.setState({
      ...state,
      [deck]: { ...state[deck], isPlaying: true }
    });
  };
};
const handlePaused = (deck: "deckA" | "deckB") => {
  return () => {
    console.log(`Track paused on ${deck}`);
    const state = store.getState();
    store.setState({
      ...state,
      [deck]: { ...state[deck], isPlaying: false }
    });
  };
};
