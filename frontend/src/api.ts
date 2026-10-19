import { sessionToken } from './auth';
import type { AnalysisJob } from './types';

export type ProfileRecord = { full_name: string; username: string; headline: string; bio: string; location: string; website: string; email: string; email_public: boolean; github_username: string; github_url: string; preferred_languages: string[]; technical_skills: string[]; interests: string[]; role: string; avatar_data_url: string; default_dashboard: string; notifications_enabled: boolean; privacy_profile_public: boolean; created_at: string; updated_at: string };
export type GitHubOverview = { login: string; name: string | null; avatar_url: string; html_url: string; public_repos: number; followers: number; following: number; bio: string | null; repositories: { name: string; html_url: string; description: string | null; language: string | null; stargazers_count: number; updated_at: string }[] };


const API_BASE = ((import.meta as ImportMeta & { env?: { VITE_API_BASE_URL?: string } }).env?.VITE_API_BASE_URL)?.replace(/\/$/, '') || 'http://localhost:8000';

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = await sessionToken();
  const headers = new Headers(init.headers);
  if (!(init.body instanceof FormData)) headers.set('Content-Type', 'application/json');
  if (token) headers.set('Authorization', `Bearer ${token}`);
  const response = await fetch(`${API_BASE}${path}`, { ...init, headers });
  const contentType = response.headers.get('content-type') || '';
  const body = contentType.includes('application/json') ? await response.json() : await response.text();
  if (!response.ok) throw new Error(typeof body === 'object' && body?.detail ? body.detail : `Request failed (${response.status}).`);
  return body as T;
}

export const api = {
  health: () => request<{ name: string; status: string; execution_mode: string; ai_provider: string }>('/api/health'),
  getProfile: () => request<ProfileRecord>('/api/profile'),
  saveProfile: (profile: ProfileRecord) => request<ProfileRecord>('/api/profile', { method: 'PUT', body: JSON.stringify(profile) }),
  githubOverview: (username: string) => request<GitHubOverview>(`/api/profile/github/${encodeURIComponent(username)}`),
  history: () => request<{ items: Record<string, unknown>[] }>('/api/analysis/history'),
  getAnalysis: (id: string) => request<AnalysisJob>(`/api/analysis/${id}`),
  submitRepo: (body: { repository_url: string; branch: string; project_label: string; include_security: boolean; include_quality: boolean; include_architecture: boolean; audience: 'mentor' | 'developer' }) => request<AnalysisJob>('/api/analysis', { method: 'POST', body: JSON.stringify(body) }),
  uploadZip: (file: File, label: string, audience: 'mentor' | 'developer', options: { include_security: boolean; include_quality: boolean; include_architecture: boolean } = { include_security: true, include_quality: true, include_architecture: true }) => {
    const form = new FormData(); form.append('file', file); form.append('project_label', label); form.append('audience', audience);
    form.append('include_security', String(options.include_security)); form.append('include_quality', String(options.include_quality)); form.append('include_architecture', String(options.include_architecture));
    return request<AnalysisJob>('/api/analysis/upload', { method: 'POST', body: form });
  },
  demo: () => request<AnalysisJob>('/api/analysis/demo', { method: 'POST' }),
  updateFinding: (jobId: string, findingId: string, status: string, note: string) => request<{id:string;status:string;note:string}>(`/api/analysis/${jobId}/findings/${findingId}`, { method: 'PATCH', body: JSON.stringify({ status, note }) }),
  askSentinal: (id: string, question: string, history: { role: 'user' | 'assistant'; content: string }[] = [], selectedPath?: string) => request<{ answer: string; provider: string; model: string }>(`/api/analysis/${id}/ask`, { method: 'POST', body: JSON.stringify({ question, history: history.slice(-6), selected_path: selectedPath }) }),
  reportUrl: (id: string) => `${API_BASE}/api/analysis/${id}/report.pdf`,
};
