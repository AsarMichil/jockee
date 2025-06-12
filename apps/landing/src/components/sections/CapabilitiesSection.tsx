import { motion } from "framer-motion";
import { Card, CardContent } from "../ui/card";
import { Badge } from "../ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../ui/tabs";
import {
  CheckCircle,
  Clock,
  Music,
  Zap,
  Cloud,
  Brain,
  Shuffle,
  BarChart3,
  Settings,
  TrendingUp
} from "lucide-react";

const currentFeatures = [
  {
    icon: Music,
    title: "Full AutoDJ Functionality",
    description:
      "Successfully progresses through entire playlists with intelligent song selection and seamless transitions.",
    status: "Production Ready"
  },
  {
    icon: Shuffle,
    title: "Multiple Transition Types",
    description:
      "Crossfade and quick cuts with framework designed for easy expansion to additional mixing techniques.",
    status: "Live"
  },
  {
    icon: Settings,
    title: "Real-time Audio Control",
    description:
      "EQ and mixing interface with responsive controls for live audio manipulation during playback.",
    status: "Active"
  },
  {
    icon: Cloud,
    title: "Cloud-based Processing",
    description:
      "Scalable song analysis and storage using AWS infrastructure with CDN distribution.",
    status: "Deployed"
  }
];

const futureRoadmap = [
  {
    icon: Brain,
    title: "ML Integration",
    description:
      "Clear architecture for trained models to improve mix point detection and song compatibility analysis.",
    timeline: "Near Future!",
    priority: "High"
  },
  {
    icon: BarChart3,
    title: "Enhanced Feature Extraction",
    description:
      "Framework ready for advanced audio analysis including tempo, key detection, and energy level mapping.",
    timeline: "Near Future!",
    priority: "Medium"
  },
  {
    icon: Zap,
    title: "Transition Strategy Expansion",
    description:
      "Modular system designed for additional mixing techniques including beat matching and harmonic mixing.",
    timeline: "Near Future!",
    priority: "High"
  },
  {
    icon: TrendingUp,
    title: "Performance Optimization",
    description:
      "Built with scalability considerations from day one, ready for horizontal scaling and load balancing.",
    timeline: "Ongoing",
    priority: "Medium"
  }
];

export function CapabilitiesSection() {
  return (
    <section id="capabilities" className="py-24">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <motion.div
          initial={{ opacity: 0, y: 50 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.8 }}
          className="text-center mb-16"
        >
          <h2 className="text-4xl lg:text-5xl font-bold mb-6 text-gray-800">
            Current Capabilities &{" "}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-brand to-brand-accent">
              Future Vision
            </span>
          </h2>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto leading-relaxed">
            A complete AutoDJ system that's production-ready today, with a clear
            roadmap for advanced features and machine learning integration.
          </p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.8, delay: 0.3 }}
        >
          <Tabs defaultValue="current" className="w-full">
            <TabsList className="grid w-full grid-cols-2 mb-8 bg-gray-100 border-gray-200">
              <TabsTrigger
                value="current"
                className="data-[state=active]:bg-white data-[state=active]:text-gray-800 text-gray-600"
              >
                What Works Now
              </TabsTrigger>
              <TabsTrigger
                value="future"
                className="data-[state=active]:bg-white data-[state=active]:text-gray-800 text-gray-600"
              >
                Technical Roadmap
              </TabsTrigger>
            </TabsList>

            <TabsContent value="current" className="space-y-8">
              <div className="grid md:grid-cols-2 gap-6">
                {currentFeatures.map((feature, index) => (
                  <motion.div
                    key={feature.title}
                    initial={{ opacity: 0, x: -30 }}
                    whileInView={{ opacity: 1, x: 0 }}
                    viewport={{ once: true }}
                    transition={{ duration: 0.6, delay: index * 0.1 }}
                  >
                    <Card className="bg-white border-gray-200 hover:shadow-lg transition-all duration-300 h-full rounded-2xl">
                      <CardContent className="p-6">
                        <div className="flex items-start space-x-4">
                          <div className="flex-shrink-0">
                            <div className="w-12 h-12 bg-gradient-to-r from-green-500 to-emerald-500 rounded-lg flex items-center justify-center">
                              <feature.icon className="w-6 h-6 text-white" />
                            </div>
                          </div>
                          <div className="flex-1">
                            <div className="flex items-center justify-between mb-2">
                              <h3 className="text-lg font-semibold text-gray-800">
                                {feature.title}
                              </h3>
                              <Badge className="bg-green-600 text-white text-xs">
                                <CheckCircle className="w-3 h-3 mr-1" />
                                {feature.status}
                              </Badge>
                            </div>
                            <p className="text-gray-600 text-sm leading-relaxed">
                              {feature.description}
                            </p>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  </motion.div>
                ))}
              </div>

              {/* Current Metrics */}
              <motion.div
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.8, delay: 0.4 }}
              >
                <Card className="bg-white border-gray-200 rounded-2xl shadow-lg">
                  <CardContent className="p-8">
                    <h3 className="text-2xl font-bold text-gray-800 mb-6 text-center">
                      Production Metrics
                    </h3>
                    <div className="grid md:grid-cols-2 gap-6 text-center">
                      {/* <div>
                        <div className="text-3xl font-bold text-green-600 mb-2">
                          100%
                        </div>
                        <p className="text-gray-600 text-sm">
                          Playlist Completion Rate
                        </p>
                      </div> */}
                      <div>
                        <div className="text-3xl font-bold text-green-600 mb-2">
                          2
                        </div>
                        <p className="text-gray-600 text-sm">
                          Transition Types Active
                        </p>
                      </div>
                      <div>
                        <div className="text-3xl font-bold text-green-600 mb-2">
                          Promise!
                        </div>
                        <p className="text-gray-600 text-sm">
                          More coming soon!
                        </p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            </TabsContent>

            <TabsContent value="future" className="space-y-8">
              <div className="grid md:grid-cols-2 gap-6">
                {futureRoadmap.map((item, index) => (
                  <motion.div
                    key={item.title}
                    initial={{ opacity: 0, x: 30 }}
                    whileInView={{ opacity: 1, x: 0 }}
                    viewport={{ once: true }}
                    transition={{ duration: 0.6, delay: index * 0.1 }}
                  >
                    <Card className="bg-white border-gray-200 hover:shadow-lg transition-all duration-300 h-full rounded-2xl">
                      <CardContent className="p-6">
                        <div className="flex items-start space-x-4">
                          <div className="flex-shrink-0">
                            <div className="w-12 h-12 bg-gradient-to-r from-blue-500 to-purple-500 rounded-lg flex items-center justify-center">
                              <item.icon className="w-6 h-6 text-white" />
                            </div>
                          </div>
                          <div className="flex-1">
                            <div className="flex items-center justify-between mb-2">
                              <h3 className="text-lg font-semibold text-gray-800">
                                {item.title}
                              </h3>
                              <div className="flex items-center space-x-2">
                                <Badge
                                  variant="outline"
                                  className={`text-xs ${
                                    item.priority === "High"
                                      ? "border-red-500 text-red-600"
                                      : "border-yellow-500 text-yellow-600"
                                  }`}
                                >
                                  {item.priority}
                                </Badge>
                                <Badge className="bg-blue-600 text-white text-xs">
                                  <Clock className="w-3 h-3 mr-1" />
                                  {item.timeline}
                                </Badge>
                              </div>
                            </div>
                            <p className="text-gray-600 text-sm leading-relaxed">
                              {item.description}
                            </p>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  </motion.div>
                ))}
              </div>
            </TabsContent>
          </Tabs>
        </motion.div>
      </div>
    </section>
  );
}
