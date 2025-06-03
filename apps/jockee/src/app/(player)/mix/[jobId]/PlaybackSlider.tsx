import { useState, useEffect } from "react";
import { Slider } from "@/components/ui/slider";
import { useAudioStore } from "@/lib/audio/AudioStoreProvider";
import { Track } from "@/lib/types";

const formatTime = (seconds: number) => {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs.toString().padStart(2, "0")}`;
};

export const PlaybackSlider = ({
  track,
  deckName
}: {
  track: Track | null;
  deckName: "A" | "B";
}) => {
  const scrubDeck = useAudioStore((state) => state.scrubDeck);
  const derivedDeckName = deckName === "A" ? "deckA" : "deckB";
  const deck = useAudioStore((state) => state[derivedDeckName]);
  const [position, setPosition] = useState([0]);
  
  const setDeckPosition = (value: number[]) => {
    scrubDeck(derivedDeckName, value[0]);
  };

  // Animation loop for continuous slider updates
  useEffect(() => {
    let animationFrameId: number;

    const animate = () => {
      // Update slider positions from audio element's currentTime
      if (deck?.audioElement) {
        const currentTime = deck.audioElement.currentTime;
        setPosition([currentTime]);
      }

      // Continue animation if deck has an audio element (whether playing or not)
      if (deck?.audioElement) {
        animationFrameId = requestAnimationFrame(animate);
      }
    };

    // Start animation loop if deck has an audio element
    if (deck?.audioElement) {
      animationFrameId = requestAnimationFrame(animate);
    }

    // Cleanup function to cancel animation frame
    return () => {
      if (animationFrameId) {
        cancelAnimationFrame(animationFrameId);
      }
    };
  }, [deck?.audioElement]);

  return (
    <div className="space-y-2">
      <div className="flex justify-between text-sm text-gray-600">
        <span>Position</span>
        <span>
          {track
            ? `${formatTime(
                Math.min(position[0], track.duration)
              )} / ${formatTime(track.duration)}`
            : "0:00 / 0:00"}
        </span>
      </div>
      <Slider
        value={position}
        onValueChange={setDeckPosition}
        max={track?.duration || 0}
        step={0.1}
        className="w-full"
        disabled={!track}
      />
    </div>
  );
};
