'use client';

import { useState, useCallback } from 'react';
import { api } from '@/lib/api';
import type { DeepAnalysis } from '@/types';
import LoadingSpinner from '@/components/ui/LoadingSpinner';
import ErrorMessage from '@/components/ui/ErrorMessage';

interface AIAnalysisPanelProps {
  articleId: string;
  initialAnalysis?: DeepAnalysis | null;
}

export default function AIAnalysisPanel({ articleId, initialAnalysis }: AIAnalysisPanelProps) {
  const [analysis, setAnalysis] = useState<DeepAnalysis | null>(initialAnalysis ?? null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const triggerAnalysis = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await api.post<DeepAnalysis>(`/articles/${articleId}/analyze`);
      setAnalysis(result);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'AI 分析失败，请稍后重试';
      setError(message);
    } finally {
      setLoading(false);
    }
  }, [articleId]);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-[13px] font-medium text-fg">AI 深度分析</h3>
        {!analysis && !loading && (
          <button
            onClick={triggerAnalysis}
            className="inline-flex items-center gap-1.5 h-7 rounded-lg bg-primary px-3 text-2xs font-medium text-white transition-colors hover:bg-primary-hover"
          >
            <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.455 2.456L21.75 6l-1.036.259a3.375 3.375 0 00-2.455 2.456z" />
            </svg>
            AI 分析
          </button>
        )}
      </div>

      {loading && (
        <div className="flex flex-col items-center justify-center py-10">
          <LoadingSpinner size="md" label="AI 正在分析中…" />
          <p className="mt-2 text-2xs text-fg-light">这可能需要几秒钟</p>
        </div>
      )}

      {!loading && error && (
        <ErrorMessage message={error} onRetry={triggerAnalysis} />
      )}

      {!loading && !error && analysis && (
        <div className="space-y-3">
          <div className="rounded-lg border border-purple-200 bg-purple-50 p-4">
            <div className="mb-1.5 flex items-center gap-1.5">
              <svg className="h-3.5 w-3.5 text-purple-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
              </svg>
              <p className="text-2xs font-medium text-purple-600">重要性</p>
            </div>
            <p className="text-[13px] leading-relaxed text-fg-secondary">{analysis.importance}</p>
          </div>

          <div className="rounded-lg border border-blue-200 bg-blue-50 p-4">
            <div className="mb-1.5 flex items-center gap-1.5">
              <svg className="h-3.5 w-3.5 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 21a9.004 9.004 0 008.716-6.747M12 21a9.004 9.004 0 01-8.716-6.747M12 21c2.485 0 4.5-4.03 4.5-9S14.485 3 12 3m0 18c-2.485 0-4.5-4.03-4.5-9S9.515 3 12 3m0 0a8.997 8.997 0 017.843 4.582M12 3a8.997 8.997 0 00-7.843 4.582m15.686 0A11.953 11.953 0 0112 10.5c-2.998 0-5.74-1.1-7.843-2.918m15.686 0A8.959 8.959 0 0121 12c0 .778-.099 1.533-.284 2.253m0 0A17.919 17.919 0 0112 16.5c-3.162 0-6.133-.815-8.716-2.247m0 0A9.015 9.015 0 013 12c0-1.605.42-3.113 1.157-4.418" />
              </svg>
              <p className="text-2xs font-medium text-blue-600">行业背景</p>
            </div>
            <p className="text-[13px] leading-relaxed text-fg-secondary">{analysis.industry_background}</p>
          </div>

          <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-4">
            <div className="mb-1.5 flex items-center gap-1.5">
              <svg className="h-3.5 w-3.5 text-emerald-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z" />
              </svg>
              <p className="text-2xs font-medium text-emerald-600">跟进建议</p>
            </div>
            <p className="text-[13px] leading-relaxed text-fg-secondary">{analysis.follow_up_suggestions}</p>
          </div>

          <div className="flex justify-end">
            <button onClick={triggerAnalysis} className="inline-flex items-center gap-1 text-2xs text-fg-muted transition-colors hover:text-fg">
              <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182" />
              </svg>
              重新分析
            </button>
          </div>
        </div>
      )}

      {!loading && !error && !analysis && (
        <div className="flex flex-col items-center justify-center rounded-lg border border-dashed border-border py-10 text-center">
          <svg className="mb-2 h-6 w-6 text-fg-light" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.455 2.456L21.75 6l-1.036.259a3.375 3.375 0 00-2.455 2.456z" />
          </svg>
          <p className="text-2xs text-fg-light">点击上方按钮启动 AI 深度分析</p>
        </div>
      )}
    </div>
  );
}
