import { motion, AnimatePresence } from "framer-motion";
import { HeroSection } from "./components/sections/HeroSection";
import { TechnicalArchitectureSection } from "./components/sections/TechnicalArchitectureSection";
import { CapabilitiesSection } from "./components/sections/CapabilitiesSection";
import { DemoSection } from "./components/sections/DemoSection";
import { Navigation } from "./components/Navigation";

function App() {
  return (
    <div className="relative min-h-screen text-gray-100 overflow-hidden">
      <Navigation />

      {/* Background Elements */}
      <div className="fixed inset-0 -z-10">
        {/* Gradient Mesh */}
        <div className="absolute inset-0 bg-gradient-mesh opacity-20" />

        {/* Animated Gradient Orbs */}
        <motion.div
          animate={{
            scale: [1, 1.2, 1],
            opacity: [0.3, 0.5, 0.3]
          }}
          transition={{
            duration: 8,
            repeat: Infinity,
            ease: "easeInOut"
          }}
          className="absolute top-1/4 left-1/4 w-[500px] h-[500px] bg-brand-primary/10 rounded-full blur-[100px]"
        />
        <motion.div
          animate={{
            scale: [1.2, 1, 1.2],
            opacity: [0.3, 0.5, 0.3]
          }}
          transition={{
            duration: 8,
            repeat: Infinity,
            ease: "easeInOut",
            delay: 1
          }}
          className="absolute bottom-1/4 right-1/4 w-[500px] h-[500px] bg-brand-secondary/10 rounded-full blur-[100px]"
        />

        {/* Grid Pattern */}
        <div
          className="absolute inset-0"
          style={{
            backgroundImage: `radial-gradient(circle at 1px 1px, rgba(255,255,255,0.05) 1px, transparent 0)`,
            backgroundSize: "40px 40px"
          }}
        />
      </div>

      {/* Content */}
      <main className="relative">
        <AnimatePresence mode="wait">
          <HeroSection />
          <TechnicalArchitectureSection />
          <CapabilitiesSection />
          <DemoSection />
        </AnimatePresence>
      </main>

      {/* Noise Texture Overlay */}
      <div
        className="pointer-events-none fixed inset-0 z-50 opacity-10"
        style={{
          backgroundImage: 'url("/noise.svg")',
          backgroundRepeat: "repeat",
          mixBlendMode: "overlay"
        }}
      />
    </div>
  );
}

export default App;
