'use client';

import { useEffect, useRef, useState } from 'react';
import mermaid from 'mermaid';
import { Loader2 } from 'lucide-react';

interface MermaidDiagramProps {
  chart: string;
}

mermaid.initialize({
  startOnLoad: true,
  theme: 'dark',
  securityLevel: 'loose',
  fontFamily: 'Inter, sans-serif',
});

export function MermaidDiagram({ chart }: MermaidDiagramProps) {
  const [svg, setSvg] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const renderChart = async () => {
      if (!chart) return;
      try {
        setLoading(true);
        const cleanChart = chart
          .replace(/```mermaid/g, '')
          .replace(/```/g, '')
          .trim();
          
        const { svg: renderedSvg } = await mermaid.render(`mermaid-${Math.random().toString(36).substr(2, 9)}`, cleanChart);
        setSvg(renderedSvg);
      } catch (err) {
        console.error('Failed to render mermaid chart:', err);
      } finally {
        setLoading(false);
      }
    };

    renderChart();
  }, [chart]);

  return (
    <div className="bg-[#111117] border border-white/10 rounded-xl p-8 min-h-[400px] flex items-center justify-center">
      {loading ? (
        <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
      ) : (
        <div 
          ref={containerRef}
          className="w-full h-full flex justify-center"
          dangerouslySetInnerHTML={{ __html: svg }} 
        />
      )}
    </div>
  );
}
