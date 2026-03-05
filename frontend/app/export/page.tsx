'use client';

import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { ArrowLeft, Download, FileJson, Archive } from 'lucide-react';

export default function ExportPage() {
  const router = useRouter();

  return (
    <div className="min-h-screen bg-[#0b0b0f] flex items-center justify-center">
      <div className="max-w-md w-full px-6 text-center">
        <div className="w-20 h-20 bg-blue-600/10 rounded-3xl flex items-center justify-center mx-auto mb-8 border border-blue-500/20">
          <Archive className="w-10 h-10 text-blue-500" />
        </div>
        <h1 className="text-3xl font-bold text-white mb-4">Export Management</h1>
        <p className="text-zinc-500 mb-8">
          This page will show your export history and allow batch downloads of documentation.
        </p>
        <Button 
          onClick={() => router.push('/')}
          className="bg-blue-600 hover:bg-blue-500 text-white w-full"
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to Home
        </Button>
      </div>
    </div>
  );
}
