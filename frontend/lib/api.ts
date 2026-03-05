import { Job, DocContent, ChatMessage } from '../types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ message: 'An unknown error occurred' }));
    throw new Error(error.message || 'API request failed');
  }

  return response.json();
}

export const api = {
  submitRepo: (repo_url: string) =>
    request<{ job_id: string }>('/repos/submit', {
      method: 'POST',
      body: JSON.stringify({ repo_url }),
    }),

  getJobStatus: (job_id: string) =>
    request<Job>(`/repos/status/${job_id}`),

  generateDoc: (job_id: string, type: string) =>
    request<DocContent>('/docs/generate', {
      method: 'POST',
      body: JSON.stringify({ job_id, type }),
    }),

  sendMessage: (job_id: string, message: string) =>
    request<ChatMessage>('/chat/message', {
      method: 'POST',
      body: JSON.stringify({ job_id, message }),
    }),

  getExportUrl: (type: 'md' | 'pdf', job_id: string) =>
    `${API_BASE_URL}/export/${type}/${job_id}`,

  createPR: (job_id: string) =>
    request<{ pr_url: string }>(`/export/pr/${job_id}`, {
      method: 'POST',
    }),
};
