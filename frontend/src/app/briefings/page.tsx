'use client';

import { useState, useEffect, useCallback } from 'react';
import { api } from '@/lib/api';
import type { DailyBriefing, PaginatedData } from '@/types';
import PageHeader from '@/components/layout/PageHeader';
import LoadingSpinner from '@/components/ui/LoadingSpinner';
import ErrorMessage from '@/components/ui/ErrorMessage';
import Pagination from '@/components/ui/Pagination';
import BriefingList from '@/components/briefings/BriefingList';

const PAGE_SIZE = 10;

export default function BriefingsPage() {
  const [briefings, setBriefings] = useState<DailyBriefing[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [generating, setGenerating] = useState(false);

  const fetchBriefings = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.get<PaginatedData<DailyBriefing>>('/briefings', { page: String(page), page_size: String(PAGE_SIZE) });
      setBriefings(data.items);
      setTotal(data.total);
    } catch {
      setError('加载简报列表失败，请稍后重试');
    } finally {
      setLoading(false);
    }
  }, [page]);

  useEffect(() => { fetchBriefings(); }, [fetchBriefings]);

  const handleGenerate = async () => {
    setGenerating(true);
    try {
      await api.post('/briefings/generate');
      setPage(1);
      await fetchBriefings();
    } catch {
      setError('生成简报失败，请稍后重试');
    } finally {
      setGenerating(false);
    }
  };

  const handlePageChange = (newPage: number) => { setPage(newPage); window.scrollTo({ top: 0, behavior: 'smooth' }); };

  return (
    <div className="space-y-6 pb-12">
      <PageHeader
        title="每日简报"
        breadcrumbs={[{ label: '首页', href: '/' }, { label: '每日简报' }]}
        actions={
          <button onClick={handleGenerate} disabled={generating}
            className="inline-flex items-center gap-2 h-8 rounded-lg bg-primary px-3 text-[13px] font-medium text-white transition-colors hover:bg-primary-hover disabled:opacity-50">
            {generating ? (
              <><svg className="h-3.5 w-3.5 animate-spin" viewBox="0 0 24 24" fill="none"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" /><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" /></svg>生成中…</>
            ) : (
              <><svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" /></svg>生成今日简报</>
            )}
          </button>
        }
      />

      {loading ? (
        <div className="flex min-h-[40vh] items-center justify-center"><LoadingSpinner size="lg" label="加载简报列表中…" /></div>
      ) : error ? (
        <ErrorMessage message={error} onRetry={fetchBriefings} />
      ) : (
        <>
          <p className="text-2xs text-fg-muted">共 <span className="font-medium text-fg-secondary">{total}</span> 份简报</p>
          <BriefingList briefings={briefings} />
          <Pagination page={page} total={total} pageSize={PAGE_SIZE} onPageChange={handlePageChange} className="mt-6" />
        </>
      )}
    </div>
  );
}
