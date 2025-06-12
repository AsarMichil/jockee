import { motion } from 'framer-motion'
import { Button } from '../ui/button'
import { Card, CardContent } from '../ui/card'
import { Separator } from '../ui/separator'
import { 
  ExternalLink, 
  Github, 
  Linkedin, 
  Play, 
  Code, 
  Mail,
  ArrowRight,
  Sparkles
} from 'lucide-react'

const demoFeatures = [
  "Live Spotify playlist integration",
  "Real-time audio mixing controls", 
  "Automated song transitions",
  "Cloud-powered audio processing"
]

const contactLinks = [
  {
    icon: Github,
    label: "GitHub Profile",
    url: "https://github.com/asarmichil",
    description: "View source code and other projects"
  },
  {
    icon: Linkedin,
    label: "LinkedIn",
    url: "https://linkedin.com/in/asarmichil", 
    description: "Professional background and experience"
  },
  {
    icon: Mail,
    label: "Email Contact",
    url: "mailto:contact@asarmichil.com",
    description: "Get in touch directly"
  }
]

export function DemoSection() {
  return (
    <section id="demo" className="py-24 bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <motion.div
          initial={{ opacity: 0, y: 50 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.8 }}
          className="text-center mb-16"
        >
          <h2 className="text-4xl lg:text-5xl font-bold mb-6 text-gray-800">
            Live Demo & <span className="text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-blue-400">Source Code</span>
          </h2>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto leading-relaxed">
            Experience the full AutoDJ system in action, then dive into the code to see how it's built. 
            Everything is open source!
          </p>
        </motion.div>

        <div className="grid lg:grid-cols-2 gap-12 items-start">
          {/* Demo Section */}
          <motion.div
            initial={{ opacity: 0, x: -50 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.8, delay: 0.2 }}
          >
            <Card className="bg-white border-gray-200 p-8 rounded-2xl shadow-lg">
              <CardContent className="space-y-6">
                <div className="text-center">
                  <div className="w-16 h-16 bg-gradient-to-r from-purple-500 to-blue-500 rounded-full flex items-center justify-center mx-auto mb-4">
                    <Play className="w-8 h-8 text-white" />
                  </div>
                  <h3 className="text-2xl font-bold text-gray-800 mb-2">
                    Try the Live Application
                  </h3>
                  <p className="text-gray-600 mb-6">
                    Full-featured AutoDJ system ready for your Spotify playlists
                  </p>
                </div>

                <div className="space-y-3">
                  {demoFeatures.map((feature, index) => (
                    <motion.div
                      key={feature}
                      initial={{ opacity: 0, x: -20 }}
                      whileInView={{ opacity: 1, x: 0 }}
                      viewport={{ once: true }}
                      transition={{ duration: 0.5, delay: 0.4 + index * 0.1 }}
                      className="flex items-center space-x-3"
                    >
                      <div className="w-2 h-2 bg-gradient-to-r from-purple-400 to-blue-400 rounded-full flex-shrink-0" />
                      <span className="text-gray-600 text-sm">{feature}</span>
                    </motion.div>
                  ))}
                </div>

                <div className="space-y-4">
                  <Button 
                    size="lg" 
                    className="w-full bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700"
                    asChild
                  >
                    <a 
                      href={import.meta.env.VITE_APP_URL} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="flex items-center justify-center space-x-2"
                    >
                      <Sparkles className="w-5 h-5" />
                      <span>Launch AutoDJ App</span>
                      <ExternalLink className="w-4 h-4" />
                    </a>
                  </Button>
                  
                  <p className="text-xs text-gray-500 text-center">
                    During development: <code className="bg-gray-100 px-2 py-1 rounded text-gray-700">localhost:3000</code>
                  </p>
                </div>
              </CardContent>
            </Card>
          </motion.div>

          {/* Code Section */}
          <motion.div
            initial={{ opacity: 0, x: 50 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.8, delay: 0.4 }}
          >
            <Card className="bg-white border-gray-200 p-8 rounded-2xl shadow-lg">
              <CardContent className="space-y-6">
                <div className="text-center">
                  <div className="w-16 h-16 bg-gradient-to-r from-gray-600 to-gray-700 rounded-full flex items-center justify-center mx-auto mb-4">
                    <Code className="w-8 h-8 text-white" />
                  </div>
                  <h3 className="text-2xl font-bold text-gray-800 mb-2">
                    Explore the Source Code
                  </h3>
                  <p className="text-gray-600 mb-6">
                    Complete codebase with documentation and deployment instructions powered by Turborepo!
                  </p>
                </div>

                <div className="bg-gray-800 rounded-lg p-4 font-mono text-sm">
                  <div className="text-green-400 mb-2"># Clone the repository</div>
                  <div className="text-gray-300 mb-3">git clone https://github.com/asarmichil/autodj</div>
                  
                  <div className="text-green-400 mb-2"># Install dependencies</div>
                  <div className="text-gray-300 mb-3">bun install</div>
                  
                  <div className="text-green-400 mb-2"># Start development server</div>
                  <div className="text-gray-300">bun dev</div>
                </div>

                <Button 
                  variant="outline" 
                  size="lg" 
                  className="w-full border-gray-300 hover:bg-gray-50 text-gray-800"
                  asChild
                >
                  <a 
                    href="https://github.com/asarmichil" 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="flex items-center justify-center space-x-2"
                  >
                    <Github className="w-5 h-5" />
                    <span>View on GitHub</span>
                    <ArrowRight className="w-4 h-4" />
                  </a>
                </Button>
              </CardContent>
            </Card>
          </motion.div>
        </div>

        {/* Contact Section */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.8, delay: 0.6 }}
          className="mt-20"
        >
          <Separator className="my-12 bg-gray-300" />
          
          <div className="text-center mb-12">
            <h3 className="text-3xl font-bold text-gray-800 mb-4">
              Let's Connect
            </h3>
            <p className="text-gray-600 max-w-2xl mx-auto">
              Interested in discussing this project, potential opportunities, or collaborating on something new? 
              I'd love to hear from you.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-6">
            {contactLinks.map((link, index) => (
              <motion.div
                key={link.label}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.6, delay: 0.8 + index * 0.1 }}
              >
                <Card className="bg-white border-gray-200 hover:shadow-lg transition-all duration-300 rounded-2xl">
                  <CardContent className="p-6 text-center">
                    <div className="w-12 h-12 bg-gradient-to-r from-purple-500 to-blue-500 rounded-lg flex items-center justify-center mx-auto mb-4">
                      <link.icon className="w-6 h-6 text-white" />
                    </div>
                    <h4 className="font-semibold text-gray-800 mb-2">
                      {link.label}
                    </h4>
                    <p className="text-gray-600 text-sm mb-4">
                      {link.description}
                    </p>
                    <Button variant="outline" size="sm" className="border-gray-300 text-gray-800 hover:bg-gray-50" asChild>
                      <a 
                        href={link.url} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="flex items-center space-x-2"
                      >
                        <span>Connect</span>
                        <ArrowRight className="w-3 h-3" />
                      </a>
                    </Button>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </div>
        </motion.div>

        {/* Footer */}
        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.8, delay: 1.0 }}
          className="mt-16 text-center"
        >
          <Separator className="my-8 bg-gray-300" />
          <p className="text-gray-600 text-sm">
            Built with React, TypeScript, Tailwind CSS, and Framer Motion. 
            Deployed on modern cloud infrastructure.
          </p>
          <p className="text-gray-500 text-xs mt-2">
            © 2025 Asar Michil.
          </p>
        </motion.div>
      </div>
    </section>
  )
} 