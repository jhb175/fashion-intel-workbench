'use client';

import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import { api } from '@/lib/api';
import type { DailyBriefing } from '@/types';
import PageHeader from '@/components/layout/PageHeader';
import LoadingSpinner from '@/components/ui/LoadingSpinner';
import ErrorMessage from '@/components/ui/ErrorMessage';
import BriefingDetail from '@/components/briefings/BriefingDetail';

export default function BriefingDetailPage() {
  const params = useParams();
  const id = params.id as string;

  const [briefing, setBriefing] = useState<DailyBriefing | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchBriefing = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.get<DailyBriefing>(`/briefings/${id}`);
      setBriefing(data);
    } catch {
      setError('加载简报详情失败，请稍后重试');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { if (id) fetchBriefing(); }, [id]); // eslint-disable-line react-hooks/exhaustive-deps

  const briefingDate = briefing
    ? new Date(briefing.briefing_date).toLocaleDateString('zh-CN', { year: 'numeric', month: 'long', day: 'numeric' })
    : '';

  return (
    <div className="space-y-6 pb-12">
      <PageHeader
        title={briefingDate ? `${briefingDate} 简报` : '简报详情'}
        breadcrumbs={[{ label: '首页', href: '/' }, { label: '每日简报', href: '/briefings' }, { label: briefingDate || '详情' }]}
      />
      {loading ? (
        <div className="flex min-h-[40vh] items-center justify-center"><LoadingSpinner size="lg" label="加载简报详情中…" /></div>
      ) : error ? (
        <ErrorMessage message={error} onRetry={fetchBriefing} />
      ) : briefing ? (
        <BriefingDetail briefing={briefing} />
      ) : null}
    </div>
  );
}
