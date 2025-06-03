import { Slider } from "@/components/ui/slider";
import { useAudioStore } from "@/lib/audio/AudioStoreProvider";
import { Track } from "@/lib/types";
import { useEffect, useState } from "react";

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
  const audioContext = useAudioStore((state) => state.audioContext);
  const scrubDeck = useAudioStore((state) => state.scrubDeck);
  //   const recalculateDeckPosition = useAudioStore(
  //     (state) => state.recalculateDeckPosition
  //   );
  const derivedDeckName = deckName === "A" ? "deckA" : "deckB";
  const deck = useAudioStore((state) => state[derivedDeckName]);
  const [position, setPosition] = useState([deck?.currentPosition || 0]);
  const setDeckPosition = (value: number[]) => {
    scrubDeck(derivedDeckName, value[0]);
  };
  // Animation loop for continuous slider updates
  useEffect(() => {
    let animationFrameId: number;

    const animate = () => {
      // Update slider positions only when decks are playing
      if (deck?.isPlaying && audioContext) {
        const currentPosition = audioContext.currentTime - deck.startTime;
        // recalculateDeckPosition(derivedDeckName);
        setPosition([currentPosition]);
      }

      // Continue animation if any deck is playing
      if (deck?.isPlaying && audioContext) {
        animationFrameId = requestAnimationFrame(animate);
      }
      if (!deck?.isPlaying && audioContext) {
        const position = deck?.currentPosition;
        if (position) {
          setPosition([position]);
        }
      }
    };

    // Start animation loop if any deck is playing
    if (deck?.isPlaying && audioContext) {
      animationFrameId = requestAnimationFrame(animate);
    }

    // Cleanup function to cancel animation frame
    return () => {
      if (animationFrameId) {
        cancelAnimationFrame(animationFrameId);
      }
    };
  }, [deck?.isPlaying, audioContext, deck, derivedDeckName]);

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
