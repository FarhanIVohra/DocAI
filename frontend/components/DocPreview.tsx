'use client';

import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { ScrollArea } from '@/components/ui/scroll-area';

interface DocPreviewProps {
  content: string;
}

export function DocPreview({ content }: DocPreviewProps) {
  return (
    <div className="bg-[#111117] border border-white/10 rounded-xl overflow-hidden h-[calc(100vh-16rem)]">
      <ScrollArea className="h-full w-full p-8">
        <article className="prose prose-invert prose-blue max-w-none prose-headings:font-bold prose-h1:text-4xl prose-h2:text-2xl prose-h3:text-xl prose-p:text-zinc-400 prose-code:text-blue-400 prose-pre:bg-black/50 prose-pre:border prose-pre:border-white/5 prose-strong:text-white prose-ul:text-zinc-400 prose-ol:text-zinc-400">
          <ReactMarkdown
            components={{
              code({ node, inline, className, children, ...props }: any) {
                const match = /language-(\w+)/.exec(className || '');
                return !inline && match ? (
                  <SyntaxHighlighter
                    style={vscDarkPlus as any}
                    language={match[1]}
                    PreTag="div"
                    className="rounded-lg border border-white/5 my-4"
                    {...props}
                  >
                    {String(children).replace(/\n$/, '')}
                  </SyntaxHighlighter>
                ) : (
                  <code className={`${className} bg-blue-500/10 text-blue-400 px-1.5 py-0.5 rounded font-mono text-sm`} {...props}>
                    {children}
                  </code>
                );
              },
            }}
          >
            {content}
          </ReactMarkdown>
        </article>
      </ScrollArea>
    </div>
  );
}
