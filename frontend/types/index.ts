export interface Job {
  job_id: string;
  repo_url: string;
  status: 'pending' | 'processing' | 'ready' | 'failed';
  progress?: number;
  created_at: string;
}

export interface DocContent {
  type: 'readme' | 'api' | 'architecture' | 'changelog' | 'onboarding' | 'audit';
  content: string;
  metadata?: any;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  sources?: string[];
  timestamp: string;
}

export interface ApiError {
  message: string;
  code?: string;
}
