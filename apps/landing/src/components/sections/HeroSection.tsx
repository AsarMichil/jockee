import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Button } from "../ui/button";
import { Badge } from "../ui/badge";
import { ExternalLink, Play, ArrowRight } from "lucide-react";
import { SiGithub } from "@icons-pack/react-simple-icons";
import DJNotPlaying from "../DJGuy/DJ-Not-Playing";
import DJPlaying from "../DJGuy/DJ-Playing";

const techStack = [
  { name: "React", color: "bg-[#61DAFB]/10 text-[#61DAFB]" },
  { name: "TypeScript", color: "bg-[#3178C6]/10 text-[#3178C6]" },
  { name: "Web Audio API", color: "bg-brand-accent/10 text-brand-accent" },
  { name: "Spotify API", color: "bg-[#1DB954]/10 text-[#1DB954]" },
  { name: "AWS S3", color: "bg-[#FF9900]/10 text-[#FF9900]" },
  { name: "CloudFront", color: "bg-[#FF9900]/10 text-[#FF9900]" },
  { name: "Python", color: "bg-[#3776AB]/10 text-[#3776AB]" },
  { name: "Framer Motion", color: "bg-brand/10 text-brand" },
  { name: "Tailwind CSS", color: "bg-[#38BDF8]/10 text-[#38BDF8]" }
];

export function HeroSection() {
  const [isPlaying, setIsPlaying] = useState(false);

  useEffect(() => {
    const interval = setInterval(() => {
      setIsPlaying((prev) => !prev);
    }, 7000);
    return () => clearInterval(interval);
  }, []);

  return (
    <section className="relative min-h-screen flex items-center justify-center pt-16 overflow-hidden">
      {/* Decorative elements */}
      <div className="absolute inset-0 -z-10">
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-gradient-radial from-brand/5 to-transparent" />
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
        <div className="grid lg:grid-cols-2 gap-16 items-center">
          {/* Left Column - Content */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            className="space-y-10"
          >
            {/* Personal Branding */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="flex items-center space-x-4"
            >
              <div className="relative">
                <div className="w-14 h-14 bg-gradient-to-r from-brand to-brand-secondary rounded-xl flex items-center justify-center shadow-lg">
                  <span className="text-white font-bold text-xl">LBP</span>
                </div>
                <motion.div
                  animate={{ scale: [1, 1.2, 1] }}
                  transition={{ duration: 2, repeat: Infinity }}
                  className="absolute -inset-1 bg-gradient-to-r from-brand to-brand-secondary rounded-xl opacity-40 blur-sm -z-10"
                />
              </div>
              <div>
                <h1 className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-brand to-brand-secondary">
                  Jockee
                </h1>
                <p className="text-gray-400">by Asar Michil</p>
              </div>
            </motion.div>

            {/* Main Headline */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4 }}
              className="space-y-6"
            >
              <h2 className="text-4xl lg:text-6xl font-bold leading-tight tracking-tight text-gray-800">
                End-to-End{" "}
                <span className="bg-clip-text text-transparent bg-gradient-to-r from-brand via-brand-secondary to-brand-accent">
                  DJ Automation
                </span>
                <span className="block mt-2 text-3xl lg:text-5xl text-gray-800">
                  From Playlists to Seamless Mixing
                </span>
              </h2>
              <p className="text-xl text-gray-800 leading-relaxed max-w-2xl">
                A comprehensive web-based DJ automation system that transforms
                Spotify playlists into professionally mixed sets using advanced
                audio analysis and intelligent transition algorithms.
              </p>
            </motion.div>

            {/* Tech Stack Badges */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.6 }}
              className="space-y-4"
            >
              <p className="text-sm font-medium text-gray-500 uppercase tracking-wider">
                Powered by Modern Tech Stack
              </p>
              <div className="flex flex-wrap gap-2">
                {techStack.map(({ name, color }, index) => (
                  <motion.div
                    key={name}
                    initial={{ opacity: 0, scale: 0.5 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{
                      type: "spring",
                      stiffness: 260,
                      damping: 20,
                      delay: 0.8 + index * 0.1
                    }}
                  >
                    <Badge
                      variant="outline"
                      className={`${color} border-0 backdrop-blur-sm font-medium`}
                    >
                      {name}
                    </Badge>
                  </motion.div>
                ))}
              </div>
            </motion.div>

            {/* CTA Buttons */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 1.0 }}
              className="flex flex-col sm:flex-row gap-4"
            >
              <Button
                size="lg"
                className="relative group bg-gradient-to-r from-brand to-brand-secondary hover:opacity-90 transition-opacity"
                asChild
              >
                <a
                  href={import.meta.env.VITE_APP_URL}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center space-x-2"
                >
                  <Play className="w-5 h-5" />
                  <span>Try Live Demo</span>
                  <ArrowRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
                </a>
              </Button>

              <Button
                size="lg"
                className="border-white/10 hover:border-white/20 backdrop-blur-sm"
                asChild
              >
                <a
                  href="https://github.com/AsarMichil/jockee"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center space-x-2"
                >
                  <SiGithub className="w-5 h-5" />
                  <span>View Source</span>
                  <ExternalLink className="w-4 h-4" />
                </a>
              </Button>
            </motion.div>

            {/* Contact Info */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 1.2 }}
              className="pt-6 border-t border-white/10"
            >
              <p className="text-sm text-gray-500">
                Connect with me:
                <a
                  href="https://linkedin.com/in/asarmichil"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-brand-accent hover:text-brand-accent/80 ml-2 transition-colors"
                >
                  linkedin.com/in/asarmichil
                </a>
              </p>
            </motion.div>
          </motion.div>

          {/* Right Column - DJ Mascot */}
          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.8, delay: 0.3 }}
            className="relative flex justify-center lg:justify-end"
          >
            <div className="relative w-full max-w-md lg:max-w-lg">
              <motion.div
                key={isPlaying ? "playing" : "not-playing"}
                initial={{ scale: 0.9, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                transition={{
                  type: "spring",
                  stiffness: 200,
                  damping: 20
                }}
                className="relative"
              >
                {isPlaying ? <DJPlaying /> : <DJNotPlaying />}

                {/* Glow effect */}
                <motion.div
                  animate={{
                    opacity: isPlaying ? [0.4, 0.6, 0.4] : 0.2
                  }}
                  transition={{
                    duration: 2,
                    repeat: Infinity,
                    ease: "easeInOut"
                  }}
                  className="absolute inset-0 -z-10 bg-gradient-to-t from-brand/20 to-brand-secondary/20 blur-2xl rounded-full"
                />
              </motion.div>

              {/* Status indicator */}
              <motion.div
                animate={{
                  scale: isPlaying ? [1, 1.1, 1] : 1,
                  opacity: isPlaying ? [0.7, 1, 0.7] : 0.5
                }}
                transition={{
                  duration: isPlaying ? 2 : 0.5,
                  repeat: isPlaying ? Infinity : 0
                }}
                className="absolute bottom-0 left-1/2 -translate-x-1/2 flex items-center justify-center space-x-2 bg-gray-900/60 backdrop-blur-md px-4 py-2 rounded-full border border-white/10"
              >
                <div
                  className={`w-2 h-2 rounded-full ${
                    isPlaying
                      ? "bg-brand-success animate-pulse"
                      : "bg-gray-900/20"
                  }`}
                />
                <span className="text-sm text-gray-300">
                  {isPlaying ? "Mixing..." : "Ready to Mix"}
                </span>
              </motion.div>
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  );
}
