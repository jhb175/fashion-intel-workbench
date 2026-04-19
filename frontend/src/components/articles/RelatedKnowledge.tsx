'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { api } from '@/lib/api';
import type { KnowledgeEntry } from '@/types';
import LoadingSpinner from '@/components/ui/LoadingSpinner';

interface RelatedKnowledgeProps {
  articleId: string;
}

const CATEGORY_LABELS: Record<string, string> = {
  brand_profile: '品牌档案',
  style_history: '风格历史',
  classic_item: '经典单品',
  person_profile: '人物档案',
};

const CATEGORY_COLORS: Record<string, string> = {
  brand_profile: 'bg-amber-50 text-amber-700 border-amber-200',
  style_history: 'bg-blue-50 text-blue-700 border-blue-200',
  classic_item: 'bg-purple-50 text-purple-700 border-purple-200',
  person_profile: 'bg-emerald-50 text-emerald-700 border-emerald-200',
};

export default function RelatedKnowledge({ articleId }: RelatedKnowledgeProps) {
  const [entries, setEntries] = useState<KnowledgeEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    let cancelled = false;
    async function fetchRelated() {
      try {
        const data = await api.get<KnowledgeEntry[]>(`/articles/${articleId}/related-knowledge`);
        const list = Array.isArray(data) ? data : [];
        if (!cancelled) setEntries(list);
      } catch {
        if (!cancelled) setError(true);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    fetchRelated();
    return () => { cancelled = true; };
  }, [articleId]);

  if (!loading && entries.length === 0 && !error) return null;
  if (error) return null;

  if (loading) {
    return <div className="py-6"><LoadingSpinner size="sm" label="加载相关背景…" /></div>;
  }

  return (
    <div className="space-y-3">
      <h3 className="text-[13px] font-medium text-fg">相关历史背景</h3>
      <div className="grid gap-2 sm:grid-cols-2">
        {entries.map((entry) => (
          <Link
            key={entry.id}
            href={`/knowledge/${entry.id}`}
            className="group block rounded-lg border border-border bg-white p-3 shadow-card transition-shadow hover:shadow-card-hover"
          >
            <div className="mb-1.5">
              <span className={`inline-block rounded-md border px-1.5 py-0.5 text-2xs font-medium ${CATEGORY_COLORS[entry.category] || 'bg-bg-hover text-fg-muted border-border'}`}>
                {CATEGORY_LABELS[entry.category] || entry.category}
              </span>
            </div>
            <h4 className="line-clamp-1 text-[13px] font-medium text-fg transition-colors group-hover:text-primary">
              {entry.title}
            </h4>
            {entry.summary && (
              <p className="mt-1 line-clamp-2 text-2xs leading-relaxed text-fg-muted">{entry.summary}</p>
            )}
          </Link>
        ))}
      </div>
    </div>
  );
}
