import { Button } from "../ui/button";
import { useAtomValue, useSetAtom } from "jotai";
import { deckAAtom, deckBAtom, setDeckBpmAtom } from "@/lib/audio/Audio";

export const BeatSyncButtons = () => {
  const deckA = useAtomValue(deckAAtom);
  const deckB = useAtomValue(deckBAtom);
  const setDeckBpm = useSetAtom(setDeckBpmAtom);
  return (
    <div className="space-y-2">
      <h3 className="text-sm font-medium text-gray-700">Sync</h3>
      <div className="grid grid-cols-2 gap-2">
        <Button
          variant="outline"
          size="sm"
          className="w-full"
          onClick={() =>
            setDeckBpm({ deck: "deckA", bpm: deckB?.track?.bpm || 0 })
          }
        >
          Beat Sync A→B
        </Button>
        <Button
          variant="outline"
          size="sm"
          className="w-full"
          onClick={() =>
            setDeckBpm({ deck: "deckB", bpm: deckA?.track?.bpm || 0 })
          }
        >
          Beat Sync B→A
        </Button>
      </div>
    </div>
  );
};
