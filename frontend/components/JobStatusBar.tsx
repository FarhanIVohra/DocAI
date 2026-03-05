'use client';

import { Loader2, CheckCircle2, AlertCircle, Clock } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';

interface JobStatusBarProps {
  status: 'pending' | 'processing' | 'ready' | 'failed';
  progress: number;
}

export function JobStatusBar({ status, progress }: JobStatusBarProps) {
  const statusConfig = {
    pending: {
      label: 'Pending',
      icon: <Clock className="w-4 h-4" />,
      className: 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20',
    },
    processing: {
      label: 'Analyzing Repository...',
      icon: <Loader2 className="w-4 h-4 animate-spin" />,
      className: 'bg-blue-500/10 text-blue-500 border-blue-500/20',
    },
    ready: {
      label: 'Analysis Complete',
      icon: <CheckCircle2 className="w-4 h-4" />,
      className: 'bg-green-500/10 text-green-500 border-green-500/20',
    },
    failed: {
      label: 'Analysis Failed',
      icon: <AlertCircle className="w-4 h-4" />,
      className: 'bg-red-500/10 text-red-500 border-red-500/20',
    },
  };

  const config = statusConfig[status] || statusConfig.pending;

  return (
    <div className="w-full bg-[#111117] border-y border-white/5 py-4 px-8 sticky top-0 z-40 backdrop-blur-xl bg-opacity-80">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center gap-6">
        <Badge className={`px-4 py-1.5 flex items-center gap-2 rounded-full border ${config.className}`}>
          {config.icon}
          {config.label}
        </Badge>
        
        {status === 'processing' && (
          <div className="flex-1 w-full space-y-2">
            <div className="flex justify-between text-xs text-zinc-500 font-medium">
              <span>Deep Analysis in Progress</span>
              <span>{progress}%</span>
            </div>
            <Progress value={progress} className="h-1.5 bg-zinc-800" />
          </div>
        )}
      </div>
    </div>
  );
}
