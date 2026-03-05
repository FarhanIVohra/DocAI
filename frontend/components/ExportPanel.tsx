'use client';

import { useState } from 'react';
import { Download, FileText, GitPullRequest, Check, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { api } from '@/lib/api';
import { toast } from 'sonner';

interface ExportPanelProps {
  jobId: string;
}

export function ExportPanel({ jobId }: ExportPanelProps) {
  const [prLoading, setPrLoading] = useState(false);
  const [prSuccess, setPrSuccess] = useState(false);

  const handleDownload = (type: 'md' | 'pdf') => {
    const url = api.getExportUrl(type, jobId);
    window.open(url, '_blank');
  };

  const handleCreatePR = async () => {
    setPrLoading(true);
    try {
      const { pr_url } = await api.createPR(jobId);
      toast.success('Pull request created successfully!');
      setPrSuccess(true);
      setTimeout(() => window.open(pr_url, '_blank'), 1500);
    } catch (err: any) {
      toast.error(err.message || 'Failed to create pull request');
    } finally {
      setPrLoading(false);
    }
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 py-8">
      <Card className="bg-[#111117] border-white/10">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <Download className="w-5 h-5 text-blue-500" />
            Markdown
          </CardTitle>
          <CardDescription className="text-zinc-500">
            Download all generated documentation as a ZIP of Markdown files.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Button 
            onClick={() => handleDownload('md')}
            className="w-full bg-blue-600 hover:bg-blue-500 text-white transition-all"
          >
            Download ZIP
          </Button>
        </CardContent>
      </Card>

      <Card className="bg-[#111117] border-white/10">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <FileText className="w-5 h-5 text-purple-500" />
            PDF Report
          </CardTitle>
          <CardDescription className="text-zinc-500">
            Export a comprehensive PDF report of the repository analysis.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Button 
            onClick={() => handleDownload('pdf')}
            className="w-full bg-purple-600 hover:bg-purple-500 text-white transition-all"
          >
            Download PDF
          </Button>
        </CardContent>
      </Card>

      <Card className="bg-[#111117] border-white/10">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <GitPullRequest className="w-5 h-5 text-green-500" />
            GitHub PR
          </CardTitle>
          <CardDescription className="text-zinc-500">
            Automatically create a Pull Request with the generated README.md.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Button 
            onClick={handleCreatePR}
            disabled={prLoading || prSuccess}
            className={`w-full transition-all ${
              prSuccess 
                ? 'bg-green-600 hover:bg-green-500 text-white' 
                : 'bg-green-600 hover:bg-green-500 text-white'
            }`}
          >
            {prLoading ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : prSuccess ? (
              <>
                <Check className="w-5 h-5 mr-2" />
                PR Created
              </>
            ) : (
              'Create PR'
            )}
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
