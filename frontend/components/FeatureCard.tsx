import { LucideIcon } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

interface FeatureCardProps {
  title: string;
  description: string;
  icon: LucideIcon;
}

export function FeatureCard({ title, description, icon: Icon }: FeatureCardProps) {
  return (
    <Card className="bg-[#111117] border-white/10 hover:border-blue-500/50 transition-all duration-300 group">
      <CardHeader>
        <div className="w-12 h-12 rounded-lg bg-blue-500/10 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
          <Icon className="w-6 h-6 text-blue-500" />
        </div>
        <CardTitle className="text-xl font-semibold text-white">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-zinc-400 leading-relaxed">
          {description}
        </p>
      </CardContent>
    </Card>
  );
}
