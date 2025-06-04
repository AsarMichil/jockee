import { createContext, ReactNode, useContext, useRef } from "react";
import { store } from "./Audio";
import { useStore } from "zustand";
import { type AudioPlayerStore } from "./Audio";

export type AudioStoreApi = typeof store;

export interface AudioStoreProviderProps {
  children: ReactNode;
}

export const AudioStoreContext = createContext<AudioStoreApi | undefined>(
  undefined
);

export const AudioStoreProvider = ({ children }: AudioStoreProviderProps) => {
  const storeRef = useRef<AudioStoreApi | null>(null);
  if (storeRef.current === null) {
    storeRef.current = store;
  }

  return (
    <AudioStoreContext.Provider value={storeRef.current}>
      {children}
    </AudioStoreContext.Provider>
  );
};

export const useAudioStore = <T,>(
  selector: (store: AudioPlayerStore) => T
): T => {
  const audioStoreContext = useContext(AudioStoreContext);

  if (!audioStoreContext) {
    throw new Error(`useAudioStore must be used within AudioStoreProvider`);
  }

  return useStore(audioStoreContext, selector);
};
