'use client';

import { Github, FileText, Layout, Code, MessageSquare, ShieldCheck, GitPullRequest } from 'lucide-react';
import { RepoInput } from '@/components/RepoInput';
import { FeatureCard } from '@/components/FeatureCard';
import { motion } from 'framer-motion';

export default function LandingPage() {
  const features = [
    {
      title: 'README Generator',
      description: 'Comprehensive, high-quality README files that explain your project architecture and goals clearly.',
      icon: Layout,
    },
    {
      title: 'API Documentation',
      description: 'Automatically extract and document your API endpoints, parameters, and response schemas.',
      icon: Code,
    },
    {
      title: 'Architecture Diagram',
      description: 'Generate beautiful Mermaid.js diagrams that visualize your system components and data flows.',
      icon: FileText,
    },
    {
      title: 'Chat with Repository',
      description: 'Ask deep technical questions about the codebase and get instant, accurate answers with sources.',
      icon: MessageSquare,
    },
    {
      title: 'Security Audit',
      description: 'Elite AI analysis to identify potential security vulnerabilities and health issues in your code.',
      icon: ShieldCheck,
    },
    {
      title: 'GitHub PR Export',
      description: 'Push generated documentation directly back to your repository with professional commit messages.',
      icon: GitPullRequest,
    },
  ];

  return (
    <main className="min-h-screen">
      {/* Hero Section */}
      <section className="relative pt-32 pb-20 overflow-hidden">
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full max-w-7xl h-[600px] pointer-events-none opacity-20">
          <div className="absolute inset-0 bg-gradient-to-b from-blue-600/50 to-transparent blur-[120px] rounded-full transform -translate-y-1/2" />
        </div>

        <div className="max-w-5xl mx-auto px-6 relative z-10 text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-400 text-sm font-medium mb-8">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-blue-500"></span>
              </span>
              Next-Gen Documentation Engine
            </div>
            
            <h1 className="text-6xl md:text-8xl font-bold tracking-tight mb-6 text-white leading-tight">
              AutoDoc <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-500 via-purple-500 to-blue-500">AI</span>
            </h1>
            <p className="text-xl md:text-2xl text-zinc-400 mb-12 max-w-2xl mx-auto leading-relaxed">
              Generate beautiful, production-ready documentation for any GitHub repository in seconds. 
              Built for the DigitalOcean Gradient AI Hackathon.
            </p>

            <RepoInput />

            <div className="mt-16 flex items-center justify-center gap-8 text-zinc-500">
              <div className="flex items-center gap-2">
                <Github className="w-5 h-5" />
                <span>Supports any public repo</span>
              </div>
              <div className="w-1 h-1 rounded-full bg-zinc-800" />
              <div className="flex items-center gap-2">
                <Code className="w-5 h-5" />
                <span>Powered by Llama 3.3</span>
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Features Grid */}
      <section className="py-24 bg-[#0b0b0f] relative border-t border-white/5">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold mb-4">Elite Documentation Suite</h2>
            <p className="text-zinc-500 max-w-xl mx-auto">Everything you need to maintain professional-grade documentation for your modern software projects.</p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map((feature, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.1 }}
              >
                <FeatureCard {...feature} />
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 border-t border-white/5 text-center text-zinc-600 text-sm">
        <p>© 2026 AutoDoc AI. Built with DigitalOcean Gradient AI.</p>
      </footer>
    </main>
  );
}
