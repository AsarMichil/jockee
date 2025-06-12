import React, { useCallback } from 'react'
import { motion } from 'framer-motion'
import { 
  ReactFlow, 
  type Node, 
  type Edge, 
  Background, 
  Controls,
  useNodesState,
  useEdgesState,
  MiniMap
} from '@xyflow/react'
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card'
import { Badge } from '../ui/badge'
import { 
  Database, 
  Cloud, 
  Music, 
  Cpu, 
  Smartphone, 
  Zap,
  Server,
  Globe,
  Brain
} from 'lucide-react'

const initialNodes: Node[] = [
  {
    id: '1',
    type: 'default',
    position: { x: 100, y: 100 },
    data: { label: 'React Frontend\n+ Shadcn/ui + Framer Motion' },
    style: { background: '#7c3aed', color: 'white', border: '2px solid #a855f7' }
  },
  {
    id: '2',
    type: 'default', 
    position: { x: 400, y: 100 },
    data: { label: 'Web Audio API\n+ Real-time EQ Controls' },
    style: { background: '#2563eb', color: 'white', border: '2px solid #3b82f6' }
  },
  {
    id: '3',
    type: 'default',
    position: { x: 100, y: 250 },
    data: { label: 'Spotify API\n+ Playlist Access' },
    style: { background: '#16a34a', color: 'white', border: '2px solid #22c55e' }
  },
  {
    id: '4',
    type: 'default',
    position: { x: 400, y: 250 },
    data: { label: 'Python Analysis Engine\n+ Audio Feature Extraction' },
    style: { background: '#dc2626', color: 'white', border: '2px solid #ef4444' }
  },
  {
    id: '5',
    type: 'default',
    position: { x: 700, y: 175 },
    data: { label: 'AWS S3 + CloudFront\n+ CDN Distribution' },
    style: { background: '#ea580c', color: 'white', border: '2px solid #f97316' }
  },
  {
    id: '6',
    type: 'default',
    position: { x: 250, y: 400 },
    data: { label: 'ML-Ready Dataset\n+ Future Model Integration' },
    style: { background: '#7c2d12', color: 'white', border: '2px solid #9a3412' }
  }
]

const initialEdges: Edge[] = [
  { id: 'e1-2', source: '1', target: '2', animated: true },
  { id: 'e1-3', source: '1', target: '3', animated: true },
  { id: 'e3-4', source: '3', target: '4', animated: true },
  { id: 'e4-5', source: '4', target: '5', animated: true },
  { id: 'e2-5', source: '2', target: '5', animated: true },
  { id: 'e4-6', source: '4', target: '6', animated: true }
]

const achievements = [
  {
    icon: Music,
    title: "Web Audio API Integration",
    description: "Built custom EQ controls with real-time audio processing, enabling seamless mixing and audio manipulation directly in the browser.",
    tech: ["Web Audio API", "JavaScript", "Real-time Processing"]
  },
  {
    icon: Smartphone,
    title: "Spotify Integration", 
    description: "Seamless playlist access and song fetching from user libraries using OAuth 2.0 authentication and REST API integration.",
    tech: ["Spotify Web API", "OAuth 2.0", "REST API"]
  },
  {
    icon: Cloud,
    title: "Cloud Storage Architecture",
    description: "S3 + CloudFront CDN for performant, scalable audio delivery with optimized caching and global distribution.",
    tech: ["AWS S3", "CloudFront CDN", "Cloud Architecture"]
  },
  {
    icon: Brain,
    title: "Python Audio Analysis Engine", 
    description: "Static song analysis identifying mix points and audio features, processing songs to create ML-ready datasets.",
    tech: ["Python", "Audio Analysis", "Feature Extraction"]
  },
  {
    icon: Zap,
    title: "Automated Mixing Logic",
    description: "Intelligent transition selection and song progression with extensible framework for multiple mixing strategies.",
    tech: ["Algorithm Design", "State Management", "Audio Processing"]
  },
  {
    icon: Server,
    title: "Extensible Architecture",
    description: "Framework ready for ML model integration and additional transition strategies with clean separation of concerns.",
    tech: ["System Architecture", "Scalability", "Extensibility"]
  }
]

export function TechnicalArchitectureSection() {
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes)
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges)

  return (
    <section id="architecture" className="py-24 bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <motion.div
          initial={{ opacity: 0, y: 50 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.8 }}
          className="text-center mb-16"
        >
          <h2 className="text-4xl lg:text-5xl font-bold mb-6 text-gray-800">
            Technical <span className="text-transparent bg-clip-text bg-gradient-to-r from-brand to-brand-accent">Architecture</span>
          </h2>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto leading-relaxed">
            A comprehensive system architecture showcasing full-stack development, 
            cloud integration, and advanced audio processing capabilities.
          </p>
        </motion.div>

        {/* Interactive System Diagram */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          whileInView={{ opacity: 1, scale: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.8, delay: 0.3 }}
          className="mb-16"
        >
          <Card className="bg-white border-gray-200 p-6 rounded-2xl shadow-lg">
            <CardHeader className="pb-4">
              <CardTitle className="text-2xl text-center text-gray-800">
                System Architecture Flow
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-96 bg-gray-900 rounded-xl border border-gray-300">
                <ReactFlow
                  nodes={nodes}
                  edges={edges}
                  onNodesChange={onNodesChange}
                  onEdgesChange={onEdgesChange}
                  fitView
                  attributionPosition="bottom-left"
                >
                  <Background color="#374151" gap={20} />
                  <Controls />
                  <MiniMap 
                    nodeColor="#7c3aed"
                    nodeStrokeWidth={3}
                    zoomable
                    pannable
                  />
                </ReactFlow>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Technical Achievements Grid */}
        <div className="space-y-12">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
            className="text-center"
          >
            <h3 className="text-3xl font-bold text-gray-800 mb-4">
              Key Technical Achievements
            </h3>
            <p className="text-gray-600 max-w-2xl mx-auto">
              Each component represents a significant engineering challenge solved 
              with modern best practices and scalable architecture.
            </p>
          </motion.div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {achievements.map((achievement, index) => (
              <motion.div
                key={achievement.title}
                initial={{ opacity: 0, y: 50 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.6, delay: index * 0.1 }}
              >
                <Card className="bg-white border-gray-200 hover:shadow-lg transition-all duration-300 h-full rounded-2xl">
                  <CardContent className="p-6">
                    <div className="flex items-start space-x-4 mb-4">
                      <div className="flex-shrink-0">
                        <div className="w-12 h-12 bg-gradient-to-r from-brand to-brand-accent rounded-lg flex items-center justify-center">
                          <achievement.icon className="w-6 h-6 text-white" />
                        </div>
                      </div>
                      <div className="flex-1">
                        <h4 className="text-lg font-semibold text-gray-800 mb-2">
                          {achievement.title}
                        </h4>
                        <p className="text-gray-600 text-sm leading-relaxed">
                          {achievement.description}
                        </p>
                      </div>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {achievement.tech.map((tech) => (
                        <Badge 
                          key={tech}
                          variant="outline" 
                          className="text-xs bg-gray-100 text-gray-700 border-gray-300"
                        >
                          {tech}
                        </Badge>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </div>
        </div>

        {/* Architecture Highlights */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.8, delay: 0.6 }}
          className="mt-16"
        >
          <Card className="bg-white border-gray-200 rounded-2xl shadow-lg">
            <CardContent className="p-8">
              <h3 className="text-2xl font-bold text-gray-800 mb-6 text-center">
                Architecture Design Principles
              </h3>
              <div className="grid md:grid-cols-3 gap-6 text-center">
                <div>
                  <div className="w-16 h-16 bg-gradient-to-r from-purple-500 to-purple-600 rounded-full flex items-center justify-center mx-auto mb-4">
                    <Zap className="w-8 h-8 text-white" />
                  </div>
                  <h4 className="font-semibold text-gray-800 mb-2">Performance First</h4>
                  <p className="text-gray-600 text-sm">
                    CDN distribution, optimized caching, and efficient audio processing for minimal latency.
                  </p>
                </div>
                <div>
                  <div className="w-16 h-16 bg-gradient-to-r from-blue-500 to-blue-600 rounded-full flex items-center justify-center mx-auto mb-4">
                    <Server className="w-8 h-8 text-white" />
                  </div>
                  <h4 className="font-semibold text-gray-800 mb-2">Scalable Design</h4>
                  <p className="text-gray-600 text-sm">
                    Cloud-native architecture with horizontal scaling capabilities and modular components.
                  </p>
                </div>
                <div>
                  <div className="w-16 h-16 bg-gradient-to-r from-green-500 to-green-600 rounded-full flex items-center justify-center mx-auto mb-4">
                    <Brain className="w-8 h-8 text-white" />
                  </div>
                  <h4 className="font-semibold text-gray-800 mb-2">Future Ready</h4>
                  <p className="text-gray-600 text-sm">
                    ML-ready data pipeline and extensible framework for advanced audio intelligence.
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>
    </section>
  )
} 