'use client';

import Link from 'next/link';
import clsx from 'clsx';
import type { KnowledgeEntry, KnowledgeCategory } from '@/types';
import EmptyState from '@/components/ui/EmptyState';
import TagBadge from '@/components/ui/TagBadge';

interface KnowledgeGridProps {
  entries: KnowledgeEntry[];
  onEdit?: (entry: KnowledgeEntry) => void;
  onDelete?: (entry: KnowledgeEntry) => void;
}

const categoryLabels: Record<KnowledgeCategory, string> = {
  brand_profile: '品牌档案', style_history: '风格历史', classic_item: '经典单品', person_profile: '人物档案',
};

const categoryColors: Record<KnowledgeCategory, string> = {
  brand_profile: 'bg-amber-50 text-amber-700 border-amber-200',
  style_history: 'bg-purple-50 text-purple-700 border-purple-200',
  classic_item: 'bg-emerald-50 text-emerald-700 border-emerald-200',
  person_profile: 'bg-blue-50 text-blue-700 border-blue-200',
};

export default function KnowledgeGrid({ entries, onEdit, onDelete }: KnowledgeGridProps) {
  if (entries.length === 0) {
    return <EmptyState title="暂无知识条目" description="当前筛选条件下没有找到知识条目，请尝试调整筛选条件" />;
  }

  return (
    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
      {entries.map((entry) => (
        <Link key={entry.id} href={`/knowledge/${entry.id}`} className="block">
          <article className="group flex flex-col rounded-lg border border-border bg-white p-4 shadow-card transition-shadow hover:shadow-card-hover">
            <span className={clsx('inline-flex w-fit items-center rounded-md border px-1.5 py-0.5 text-2xs font-medium', categoryColors[entry.category])}>
              {categoryLabels[entry.category]}
            </span>
            <h3 className="mt-2 line-clamp-2 text-[13px] font-medium leading-relaxed text-fg transition-colors group-hover:text-primary">{entry.title}</h3>
            {entry.summary && <p className="mt-1.5 line-clamp-3 flex-1 text-2xs leading-relaxed text-fg-muted">{entry.summary}</p>}
            <div className="mt-2 flex flex-wrap gap-1">
              {entry.brands.slice(0, 3).map((brand) => <TagBadge key={brand} label={brand} variant="brand" />)}
              {entry.keywords.slice(0, 2).map((kw) => <TagBadge key={kw} label={kw} variant="keyword" />)}
              {entry.brands.length + entry.keywords.length > 5 && <span className="inline-flex items-center text-2xs text-fg-light">+{entry.brands.length + entry.keywords.length - 5}</span>}
            </div>
            <div className="mt-3 flex items-center justify-between border-t border-border pt-3">
              <time className="text-2xs text-fg-light">{new Date(entry.updated_at).toLocaleDateString('zh-CN', { year: 'numeric', month: 'short', day: 'numeric' })}</time>
              {(onEdit || onDelete) && (
                <div className="flex items-center gap-1 opacity-0 transition-opacity group-hover:opacity-100">
                  {onEdit && <button onClick={(e) => { e.preventDefault(); e.stopPropagation(); onEdit(entry); }} className="rounded-md px-2 py-1 text-2xs font-medium text-fg-secondary transition-colors hover:bg-bg-hover">编辑</button>}
                  {onDelete && <button onClick={(e) => { e.preventDefault(); e.stopPropagation(); onDelete(entry); }} className="rounded-md px-2 py-1 text-2xs font-medium text-red-500 transition-colors hover:bg-red-50">删除</button>}
                </div>
              )}
            </div>
          </article>
        </Link>
      ))}
    </div>
  );
}
