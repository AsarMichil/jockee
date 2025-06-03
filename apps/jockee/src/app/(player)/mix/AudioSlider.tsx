import { Slider } from "@/components/ui/slider";
import { useAudioStore } from "@/lib/audio/AudioStoreProvider";
import { Volume2 } from "lucide-react";
import { useEffect, useState } from "react";

export const AudioSlider = ({ deckName }: { deckName: "A" | "B" }) => {
  const audioContext = useAudioStore((state) => state.audioContext);
  const derivedDeckName = deckName === "A" ? "deckA" : "deckB";
  const deck = useAudioStore((state) => state[derivedDeckName]);
  const setDeckVolume = useAudioStore((state) => state.setDeckVolume);
  const [volume, setVolume] = useState([deck?.audioElement?.volume || 0]);
  const setVolumeHandler = (value: number[]) => {
    const newVolume = value[0] / 100;
    setVolume(value);
    setDeckVolume(derivedDeckName, newVolume);
  };
  console.log("deck", deck);
  // Animation loop for continuous slider updates
  useEffect(() => {
    let animationFrameId: number;

    const animate = () => {
      // Update slider positions only when decks are playing
      if (deck?.isAnimating && audioContext) {
        const currentVolume = deck.audioElement?.volume || 0;
        setVolume([currentVolume]);
      }

      // Continue animation if any deck is playing
      if (deck?.isAnimating && audioContext) {
        animationFrameId = requestAnimationFrame(animate);
      }
      if (!deck?.isAnimating && audioContext) {
        const volume = deck?.audioElement?.volume || 0;
        if (volume) {
          setVolume([volume]);
        }
      }
    };

    // Start animation loop if any deck is playing
    if (deck?.isAnimating && audioContext) {
      animationFrameId = requestAnimationFrame(animate);
    }

    // Cleanup function to cancel animation frame
    return () => {
      if (animationFrameId) {
        cancelAnimationFrame(animationFrameId);
      }
    };
  }, [deck?.isAnimating, audioContext, deck, derivedDeckName]);

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <label className="text-sm font-medium text-gray-700 flex items-center">
          <Volume2 className="h-4 w-4 mr-1" />
          Volume
        </label>
        <span className="text-sm text-gray-500">{volume[0]}%</span>
      </div>
      <Slider
        value={volume}
        onValueChange={setVolumeHandler}
        max={100}
        step={1}
        className="w-full"
      />
    </div>
  );
};
