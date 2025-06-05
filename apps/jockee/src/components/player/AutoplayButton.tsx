import { useAtom } from "jotai";
import { autoplayAtom } from "@/lib/audio/Audio";
import { Button } from "../ui/button";

export const AutoplayButton = () => {
  const [autoplay, setAutoplay] = useAtom(autoplayAtom);
  return (
    <Button
      variant={autoplay ? "default" : "outline"}
      onClick={() => setAutoplay((prev) => !prev)}
    >
      {autoplay ? "Disable Autoplay" : "Enable Autoplay"}
    </Button>
  );
};
