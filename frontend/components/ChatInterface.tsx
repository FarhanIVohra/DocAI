'use client';

import { useState, useRef, useEffect } from 'react';
import { Send, User, Bot, Loader2, Link as LinkIcon } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { api } from '@/lib/api';
import { useJobStore } from '@/store/jobStore';
import { toast } from 'sonner';

interface ChatInterfaceProps {
  jobId: string;
}

export function ChatInterface({ jobId }: ChatInterfaceProps) {
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const messages = useJobStore((state) => state.chatMessages);
  const addMessage = useJobStore((state) => state.addChatMessage);

  useEffect(() => {
    console.log('Messages updated:', messages);
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMessage = {
      id: Date.now().toString(),
      role: 'user' as const,
      content: input,
      timestamp: new Date().toISOString(),
    };

    addMessage(userMessage);
    setInput('');
    setLoading(true);

    try {
      const response = await api.sendMessage(jobId, input);
      addMessage(response);
    } catch (err: any) {
      toast.error(err.message || 'Failed to send message');
    } finally {
      setLoading(false);
      console.log('Loading state after response:', loading);
    }
  };

  return (
    <div className="flex flex-col bg-[#111117] border border-white/10 rounded-xl overflow-hidden">
      <ScrollArea className="flex-1 p-6" ref={scrollRef}>
        <div className="space-y-6">
          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center h-full text-zinc-500 py-12 text-center">
              <Bot className="w-12 h-12 mb-4 text-blue-500/50" />
              <p className="max-w-xs">Ask me anything about this repository's codebase.</p>
            </div>
          )}
          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex gap-4 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`flex max-w-[80%] gap-3 ${
                  msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'
                }`}
              >
                <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                  msg.role === 'user' ? 'bg-blue-600' : 'bg-zinc-800'
                }`}>
                  {msg.role === 'user' ? <User className="w-5 h-5" /> : <Bot className="w-5 h-5 text-blue-400" />}
                </div>
                <div className="space-y-2">
                  <div className={`p-4 rounded-2xl ${
                    msg.role === 'user' 
                      ? 'bg-blue-600 text-white rounded-tr-none' 
                      : 'bg-zinc-800 text-zinc-200 rounded-tl-none'
                  }`}>
                    <p className="leading-relaxed whitespace-pre-wrap">{msg.content}</p>
                  </div>
                  {msg.sources && msg.sources.length > 0 && (
                    <div className="flex flex-wrap gap-2 pt-1">
                      {msg.sources.map((source, i) => (
                        <div key={`${source}-${i}`} className="flex items-center gap-1.5 px-2 py-1 rounded bg-zinc-900 border border-white/5 text-[10px] text-zinc-500 font-mono">
                          <LinkIcon className="w-3 h-3" />
                          {source}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
          {loading && (
            <div className="flex gap-4 justify-start">
              <div className="w-8 h-8 rounded-full bg-zinc-800 flex items-center justify-center">
                <Bot className="w-5 h-5 text-blue-400" />
              </div>
              <div className="bg-zinc-800 p-4 rounded-2xl rounded-tl-none">
                <Loader2 className="w-5 h-5 text-blue-500 animate-spin" />
              </div>
            </div>
          )}
        </div>
      </ScrollArea>

      <form onSubmit={handleSend} className="p-4 border-t border-white/10 bg-[#0b0b0f]">
        <div className="relative flex items-center gap-2">
          <Input
            value={input}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) => setInput(e.target.value)}
            placeholder="Ask a question about the repository..."
            className="flex-1 bg-[#111117] border-white/10 text-white focus-visible:ring-blue-500 h-12"
          />
          <Button
            type="submit"
            disabled={loading || !input.trim()}
            className="bg-blue-600 hover:bg-blue-500 text-white w-12 h-12 p-0 flex-shrink-0"
          >
            <Send className="w-5 h-5" />
          </Button>
        </div>
      </form>
    </div>
  );
}
