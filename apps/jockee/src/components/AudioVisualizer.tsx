import { useEffect, useRef } from 'react';

interface AudioVisualizerProps {
  isPlaying: boolean;
  className?: string;
}

export const AudioVisualizer: React.FC<AudioVisualizerProps> = ({ 
  isPlaying, 
  className = '' 
}) => {
  const barsRef = useRef<HTMLDivElement[]>([]);
  const animationRef = useRef<number | null>(null);

  useEffect(() => {
    const animateBars = () => {
      if (!isPlaying) {
        // Reset bars to minimum height when not playing
        barsRef.current.forEach(bar => {
          if (bar) {
            bar.style.height = '4px';
          }
        });
        return;
      }

      // Animate bars with random heights when playing
      barsRef.current.forEach(bar => {
        if (bar) {
          const height = Math.random() * 32 + 4; // 4px to 36px
          bar.style.height = `${height}px`;
        }
      });

      animationRef.current = requestAnimationFrame(animateBars);
    };

    if (isPlaying) {
      animateBars();
    } else {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
      animateBars(); // Reset bars
    }

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [isPlaying]);

  return (
    <div className={`flex items-end space-x-1 h-10 ${className}`}>
      {Array.from({ length: 12 }).map((_, index) => (
        <div
          key={index}
          ref={el => {
            if (el) barsRef.current[index] = el;
          }}
          className="bg-blue-500 w-1 transition-all duration-75 ease-out"
          style={{ height: '4px' }}
        />
      ))}
    </div>
  );
}; 