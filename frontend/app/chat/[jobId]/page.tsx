'use client';

import { use, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { ArrowLeft, Bot, Github } from 'lucide-react';
import { ChatInterface } from '@/components/ChatInterface';
import { Button } from '@/components/ui/button';
import { useJobStore } from '@/store/jobStore';
import { api } from '@/lib/api';

interface PageProps {
  params: Promise<{ jobId: string }>;
}

export default function ChatPage({ params }: PageProps) {
  const { jobId } = use(params);
  const router = useRouter();
  const { status, setStatus, setJobId } = useJobStore();

  useEffect(() => {
    setJobId(jobId);
    if (!status) {
      api.getJobStatus(jobId).then(j => setStatus(j.status)).catch(() => {});
    }
  }, [jobId]);

  return (
    <div className="min-h-screen bg-[#0b0b0f]">
      <div className="max-w-6xl mx-auto px-6 py-8 h-screen flex flex-col">
        <header className="flex items-center justify-between mb-8">
          <div className="flex items-center gap-6">
            <Button
              variant="ghost"
              onClick={() => router.push(`/docs/${jobId}`)}
              className="text-zinc-400 hover:text-white hover:bg-white/5"
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Docs
            </Button>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-blue-600/10 flex items-center justify-center border border-blue-500/20">
                <Bot className="w-6 h-6 text-blue-500" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-white">Repository Assistant</h1>
                <p className="text-xs text-zinc-500">Job ID: {jobId}</p>
              </div>
            </div>
          </div>
          
          <div className="flex items-center gap-3 px-3 py-1.5 rounded-full bg-green-500/10 border border-green-500/20 text-green-500 text-xs font-medium">
            <span className="relative flex h-2 w-2">
              <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
            </span>
            Context Loaded
          </div>
        </header>

        <main className="flex-1 min-h-0">
          <ChatInterface jobId={jobId} />
        </main>
        
        <footer className="mt-6 text-center text-xs text-zinc-600">
          Our AI assistant has indexed this repository and provides answers based on the code analysis.
        </footer>
      </div>
    </div>
  );
}
