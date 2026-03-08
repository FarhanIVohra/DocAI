'use client';

import { useEffect, useState, use } from 'react';
import { useRouter } from 'next/navigation';
import {
  Layout, Code, FileText, History, UserPlus,
  ShieldCheck, MessageSquare, Download, Loader2
} from 'lucide-react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { JobStatusBar } from '@/components/JobStatusBar';
import { DocPreview } from '@/components/DocPreview';
import { MermaidDiagram } from '@/components/MermaidDiagram';
import { ChatInterface } from '@/components/ChatInterface';
import { ExportPanel } from '@/components/ExportPanel';
import { api } from '@/lib/api';
import { useJobStore } from '@/store/jobStore';
import { toast } from 'sonner';
import { Skeleton } from '@/components/ui/skeleton';

interface PageProps {
  params: Promise<{ jobId: string }>;
}

export default function DocsPage({ params }: PageProps) {
  const { jobId } = use(params);
  const router = useRouter();
  const {
    status, progress, docs, setStatus, setProgress, setDoc, setJobId
  } = useJobStore();

  const [activeTab, setActiveTab] = useState('readme');
  const [docLoading, setDocLoading] = useState(false);

  // Poll job status
  useEffect(() => {
    setJobId(jobId);
    let pollInterval: NodeJS.Timeout;

    const checkStatus = async () => {
      try {
        const job = await api.getJobStatus(jobId);
        setStatus(job.status);
        if (job.progress) setProgress(job.progress);

        if (job.status === 'ready' || job.status === 'failed') {
          clearInterval(pollInterval);
          if (job.status === 'ready') {
            toast.success('Analysis complete! Your documentation is ready.');
            fetchDoc('readme');
          } else {
            toast.error('Analysis failed. Please try again.');
          }
        }
      } catch (err: any) {
        console.error('Status poll error:', err);
      }
    };

    checkStatus();
    pollInterval = setInterval(checkStatus, 3000);

    return () => clearInterval(pollInterval);
  }, [jobId]);

  const fetchDoc = async (type: string) => {
    if (docs[type] || status !== 'ready') return;

    setDocLoading(true);
    try {
      const { content } = await api.generateDoc(jobId, type);
      setDoc(type, content);
    } catch (err: any) {
      toast.error(`Failed to load ${type} documentation`);
    } finally {
      setDocLoading(false);
    }
  };

  const handleTabChange = (value: string) => {
    setActiveTab(value);
    if (['readme', 'api', 'architecture', 'changelog', 'onboarding', 'audit'].includes(value)) {
      fetchDoc(value);
    }
  };

  return (
    <div className="min-h-screen bg-[#0b0b0f] pb-20">
      <JobStatusBar status={status || 'pending'} progress={progress} />

      <div className="max-w-7xl mx-auto px-6 pt-8">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-white mb-2">Repository Documentation</h1>
            <p className="text-zinc-500">Job ID: <code className="text-blue-500">{jobId}</code></p>
          </div>
          <div className="flex gap-3">
            <button
              onClick={() => router.push(`/chat/${jobId}`)}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600/10 text-blue-400 border border-blue-500/20 rounded-lg hover:bg-blue-600/20 transition-all"
            >
              <MessageSquare className="w-4 h-4" />
              Interactive Chat
            </button>
          </div>
        </div>

        <Tabs value={activeTab} onValueChange={handleTabChange} className="space-y-8">
          <TabsList className="bg-[#111117] border border-white/5 p-1 h-auto flex-wrap justify-start">
            <TabsTrigger value="readme" className="data-[state=active]:bg-blue-600 gap-2 py-2.5 px-5">
              <Layout className="w-4 h-4" /> README
            </TabsTrigger>
            <TabsTrigger value="api" className="data-[state=active]:bg-blue-600 gap-2 py-2.5 px-5">
              <Code className="w-4 h-4" /> API Docs
            </TabsTrigger>
            <TabsTrigger value="architecture" className="data-[state=active]:bg-blue-600 gap-2 py-2.5 px-5">
              <FileText className="w-4 h-4" /> Architecture
            </TabsTrigger>
            <TabsTrigger value="changelog" className="data-[state=active]:bg-blue-600 gap-2 py-2.5 px-5">
              <History className="w-4 h-4" /> Changelog
            </TabsTrigger>
            <TabsTrigger value="onboarding" className="data-[state=active]:bg-blue-600 gap-2 py-2.5 px-5">
              <UserPlus className="w-4 h-4" /> Onboarding
            </TabsTrigger>
            <TabsTrigger value="audit" className="data-[state=active]:bg-blue-600 gap-2 py-2.5 px-5">
              <ShieldCheck className="w-4 h-4" /> Security Audit
            </TabsTrigger>
            <TabsTrigger value="export" className="data-[state=active]:bg-blue-600 gap-2 py-2.5 px-5">
              <Download className="w-4 h-4" /> Export
            </TabsTrigger>
          </TabsList>

          <div className="relative min-h-[500px]">
            {status === 'failed' ? (
              <div className="flex flex-col items-center justify-center p-16 bg-red-500/5 border border-red-500/20 rounded-xl mt-4">
                <ShieldCheck className="w-12 h-12 text-red-400 mb-4" />
                <h3 className="text-xl font-bold text-red-500 mb-2">Analysis Failed</h3>
                <p className="text-red-400/80 text-center max-w-md mb-6">
                  There was an error processing this repository. It may be too large, private, or the AI service may have timed out.
                </p>
                <button
                  onClick={() => router.push('/')}
                  className="px-6 py-2 bg-red-600/20 hover:bg-red-600/30 text-red-400 rounded-lg transition-colors border border-red-500/30"
                >
                  Return Home
                </button>
              </div>
            ) : status !== 'ready' ? (
              <div className="space-y-4">
                <Skeleton className="h-12 w-3/4 bg-white/5" />
                <Skeleton className="h-[400px] w-full bg-white/5" />
              </div>
            ) : (
              <>
                <TabsContent value="readme" className="mt-0">
                  {docLoading && !docs.readme ? <DocSkeleton /> : <DocPreview content={docs.readme || ''} />}
                </TabsContent>
                <TabsContent value="api" className="mt-0">
                  {docLoading && !docs.api ? <DocSkeleton /> : <DocPreview content={docs.api || ''} />}
                </TabsContent>
                <TabsContent value="architecture" className="mt-0">
                  {docLoading && !docs.architecture ? <DocSkeleton /> : <MermaidDiagram chart={docs.architecture || ''} />}
                </TabsContent>
                <TabsContent value="changelog" className="mt-0">
                  {docLoading && !docs.changelog ? <DocSkeleton /> : <DocPreview content={docs.changelog || ''} />}
                </TabsContent>
                <TabsContent value="onboarding" className="mt-0">
                  {docLoading && !docs.onboarding ? <DocSkeleton /> : <DocPreview content={docs.onboarding || ''} />}
                </TabsContent>
                <TabsContent value="audit" className="mt-0">
                  {docLoading && !docs.audit ? <DocSkeleton /> : <DocPreview content={docs.audit || ''} />}
                </TabsContent>
                <TabsContent value="export" className="mt-0">
                  <ExportPanel jobId={jobId} />
                </TabsContent>
              </>
            )}
          </div>
        </Tabs>
      </div>
    </div>
  );
}

function DocSkeleton() {
  return (
    <div className="space-y-6 p-8 bg-[#111117] border border-white/10 rounded-xl">
      <Skeleton className="h-10 w-1/3 bg-white/5" />
      <div className="space-y-3">
        <Skeleton className="h-4 w-full bg-white/5" />
        <Skeleton className="h-4 w-5/6 bg-white/5" />
        <Skeleton className="h-4 w-4/6 bg-white/5" />
      </div>
      <Skeleton className="h-6 w-1/4 bg-white/5 mt-8" />
      <div className="space-y-3">
        <Skeleton className="h-4 w-full bg-white/5" />
        <Skeleton className="h-4 w-full bg-white/5" />
        <Skeleton className="h-4 w-3/4 bg-white/5" />
      </div>
    </div>
  );
}
