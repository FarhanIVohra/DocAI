'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Github, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { api } from '@/lib/api';
import { useJobStore } from '@/store/jobStore';
import { toast } from 'sonner';

export function RepoInput() {
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const router = useRouter();
  const setJobId = useJobStore((state) => state.setJobId);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url || !url.includes('github.com')) {
      toast.error('Please enter a valid GitHub repository URL');
      return;
    }

    setLoading(true);
    try {
      const { job_id } = await api.submitRepo(url);
      setJobId(job_id);
      router.push(`/docs/${job_id}`);
    } catch (err: any) {
      toast.error(err.message || 'Failed to submit repository');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="w-full max-w-2xl mx-auto space-y-4">
      <div className="relative group">
        <div className="absolute inset-0 bg-blue-500/20 blur-xl group-focus-within:bg-blue-500/30 transition-all rounded-full" />
        <div className="relative flex items-center bg-[#111117] border border-white/10 rounded-full px-4 py-2 group-focus-within:border-blue-500/50 transition-all">
          <Github className="w-6 h-6 text-zinc-500 mr-3" />
          <Input
            value={url}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) => setUrl(e.target.value)}
            placeholder="https://github.com/user/project"
            className="flex-1 bg-transparent border-none text-white focus-visible:ring-0 placeholder:text-zinc-600 h-12 text-lg"
          />
          <Button
            type="submit"
            disabled={loading}
            className="ml-4 bg-blue-600 hover:bg-blue-500 text-white rounded-full px-8 h-12 text-lg font-medium transition-all hover:scale-105 active:scale-95 disabled:opacity-50"
          >
            {loading ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              'Generate Docs'
            )}
          </Button>
        </div>
      </div>
    </form>
  );
}
