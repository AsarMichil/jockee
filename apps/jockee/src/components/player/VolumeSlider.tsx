import { Volume2 } from "lucide-react";
import { Slider } from "@/components/ui/slider";
import {
  deckAVolumeAtom,
  deckBVolumeAtom,
  setDeckVolumeAtom
} from "@/lib/audio/Audio";
import { useAtomValue, useSetAtom } from "jotai";

interface VolumeSliderProps {
  label?: string;
  className?: string;
  deckName: "A" | "B";
}

export default function VolumeSlider({
  label = "Volume",
  className = "",
  deckName
}: VolumeSliderProps) {
  const setDeckVolume = useSetAtom(setDeckVolumeAtom);
  const volume = useAtomValue(
    deckName === "A" ? deckAVolumeAtom : deckBVolumeAtom
  );

  const setVolume = (value: number[]) => {
    console.log("setVolume", value);

    setDeckVolume({
      deck: deckName === "A" ? "deckA" : "deckB",
      volume: value[0]
    });
  };

  return (
    <div className={`space-y-2 ${className}`}>
      <div className="flex items-center justify-between">
        <label className="text-sm font-medium text-gray-700 flex items-center">
          <Volume2 className="h-4 w-4 mr-1" />
          {label}
        </label>
        <span className="text-sm text-gray-500">{volume * 100}%</span>
      </div>
      <Slider
        value={[volume]}
        onValueChange={setVolume}
        max={1}
        min={0}
        step={0.01}
        className="w-full"
      />
    </div>
  );
}
