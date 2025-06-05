import { Button } from "../ui/button";
import { useAtomValue, useSetAtom } from "jotai";
import {
  deckAAtom,
  deckBAtom,
  playPauseDeckAtom
} from "@/lib/audio/Audio";

export const BigAssPlayButton = ({
  isPlaying,
  disabled,
  onClick
}: {
  isPlaying: boolean;
  disabled: boolean;
  onClick: () => void;
}) => {
  return (
    <Button disabled={disabled} onClick={onClick}>
      {isPlaying ? "Pause" : "Play"}
    </Button>
  );
};
export const APlayButton = () => {
  const deckState = useAtomValue(deckAAtom);
  const setPlayPause = useSetAtom(playPauseDeckAtom);

  return (
    <BigAssPlayButton
      isPlaying={deckState?.isPlaying || false}
      disabled={!deckState}
      onClick={() => setPlayPause("deckA")}
    />
  );
};
export const BPlayButton = () => {
  const deckState = useAtomValue(deckBAtom);
  const setPlayPause = useSetAtom(playPauseDeckAtom);

  return (
    <BigAssPlayButton
      isPlaying={deckState?.isPlaying || false}
      disabled={!deckState}
      onClick={() => setPlayPause("deckB")}
    />
  );
};
