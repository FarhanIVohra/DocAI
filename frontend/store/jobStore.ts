import { create } from 'zustand';
import { Job, ChatMessage, DocContent } from '../types';

interface JobState {
  jobId: string | null;
  status: Job['status'] | null;
  progress: number;
  docs: Record<string, string>;
  chatMessages: ChatMessage[];
  error: string | null;

  setJobId: (id: string | null) => void;
  setStatus: (status: Job['status']) => void;
  setProgress: (progress: number) => void;
  setDoc: (type: string, content: string) => void;
  addChatMessage: (message: ChatMessage) => void;
  setError: (error: string | null) => void;
  reset: () => void;
}

export const useJobStore = create<JobState>((set) => ({
  jobId: null,
  status: null,
  progress: 0,
  docs: {},
  chatMessages: [],
  error: null,

  setJobId: (id) => set({ jobId: id }),
  setStatus: (status) => set({ status }),
  setProgress: (progress) => set({ progress }),
  setDoc: (type, content) =>
    set((state) => ({
      docs: { ...state.docs, [type]: content },
    })),
  addChatMessage: (message) =>
    set((state) => ({
      chatMessages: [...state.chatMessages, message],
    })),
  setError: (error) => set({ error }),
  reset: () =>
    set({
      jobId: null,
      status: null,
      progress: 0,
      docs: {},
      chatMessages: [],
      error: null,
    }),
}));
