'use client';

import { useState, type FormEvent } from 'react';
import { useRouter } from 'next/navigation';
import { setToken } from '@/lib/auth';
import { api } from '@/lib/api';

export default function LoginPage() {
  const router = useRouter();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const data = await api.post<{ access_token: string }>('/auth/login', { username, password });
      setToken(data.access_token);
      router.replace('/');
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : '登录失败，请检查用户名和密码');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-bg">
      <div className="w-full max-w-sm px-6">
        {/* Brand */}
        <div className="mb-10 text-center">
          <div className="mx-auto mb-3 flex h-10 w-10 items-center justify-center rounded-lg bg-primary">
            <span className="text-base font-medium text-white">潮</span>
          </div>
          <h1 className="text-lg font-medium tracking-tight text-fg">潮流情报</h1>
          <p className="mt-1 text-2xs text-fg-light uppercase tracking-widest">Fashion Intel Workbench</p>
        </div>

        {/* Login card */}
        <div className="rounded-lg border border-border bg-white p-6 shadow-card">
          <h2 className="mb-6 text-center text-[13px] font-medium text-fg-secondary">登录工作台</h2>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label htmlFor="username" className="mb-1 block text-2xs font-medium text-fg-muted">用户名</label>
              <input id="username" type="text" required autoComplete="username" value={username}
                onChange={(e) => setUsername(e.target.value)} placeholder="请输入用户名"
                className="h-8 w-full rounded-lg border border-border bg-bg px-3 text-[13px] text-fg placeholder:text-fg-light focus:border-primary/50 focus:outline-none focus:ring-1 focus:ring-primary/20" />
            </div>
            <div>
              <label htmlFor="password" className="mb-1 block text-2xs font-medium text-fg-muted">密码</label>
              <input id="password" type="password" required autoComplete="current-password" value={password}
                onChange={(e) => setPassword(e.target.value)} placeholder="请输入密码"
                className="h-8 w-full rounded-lg border border-border bg-bg px-3 text-[13px] text-fg placeholder:text-fg-light focus:border-primary/50 focus:outline-none focus:ring-1 focus:ring-primary/20" />
            </div>

            {error && (
              <p className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-center text-[13px] text-red-600">
                {error}
              </p>
            )}

            <button type="submit" disabled={loading}
              className="h-8 w-full rounded-lg bg-primary text-[13px] font-medium text-white transition-colors hover:bg-primary-hover disabled:opacity-50">
              {loading ? (
                <span className="flex items-center justify-center gap-2">
                  <svg className="h-3.5 w-3.5 animate-spin" viewBox="0 0 24 24" fill="none">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                  登录中…
                </span>
              ) : '登录'}
            </button>
          </form>
        </div>

        <p className="mt-6 text-center text-2xs text-fg-light">
          全球时尚潮流资讯 AI 情报平台
        </p>
      </div>
    </div>
  );
}
