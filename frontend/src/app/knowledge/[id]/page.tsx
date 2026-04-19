'use client';

import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import { api } from '@/lib/api';
import type { KnowledgeEntry } from '@/types';
import PageHeader from '@/components/layout/PageHeader';
import LoadingSpinner from '@/components/ui/LoadingSpinner';
import ErrorMessage from '@/components/ui/ErrorMessage';
import KnowledgeDetail from '@/components/knowledge/KnowledgeDetail';

const categoryLabels: Record<string, string> = {
  brand_profile: '品牌档案',
  style_history: '风格历史',
  classic_item: '经典单品',
  person_profile: '人物档案',
};

export default function KnowledgeDetailPage() {
  const params = useParams();
  const id = params.id as string;
  const [entry, setEntry] = useState<KnowledgeEntry | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchEntry = async () => {
    setLoading(true);
    setError(null);
    try { const data = await api.get<KnowledgeEntry>(`/knowledge/${id}`); setEntry(data); }
    catch { setError('加载知识条目失败，请稍后重试'); }
    finally { setLoading(false); }
  };

  useEffect(() => { if (id) fetchEntry(); }, [id]); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div className="space-y-6 pb-12">
      <PageHeader title={entry?.title || '知识条目详情'}
        breadcrumbs={[{ label: '首页', href: '/' }, { label: '知识库', href: '/knowledge' }, { label: entry ? categoryLabels[entry.category] || entry.category : '详情' }]} />
      {loading ? (
        <div className="flex min-h-[40vh] items-center justify-center"><LoadingSpinner size="lg" label="加载知识条目中…" /></div>
      ) : error ? (
        <ErrorMessage message={error} onRetry={fetchEntry} />
      ) : entry ? (
        <KnowledgeDetail entry={entry} />
      ) : null}
    </div>
  );
}
