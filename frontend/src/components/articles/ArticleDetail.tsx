'use client';

import type { Article } from '@/types';
import BrandNamingBadge from '@/components/brands/BrandNamingBadge';

function formatDate(dateStr: string | null): string {
  if (!dateStr) return '未知';
  return new Date(dateStr).toLocaleDateString('zh-CN', { year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit' });
}

export default function ArticleDetail({ article }: { article: Article }) {
  const brandTags = article.tags.filter((t) => t.tag_type === 'brand');

  return (
    <div className="space-y-6">
      {/* 中文摘要 */}
      <div>
        <h2 className="text-lg font-medium leading-relaxed text-fg">
          {article.chinese_summary || article.original_title}
        </h2>
        {brandTags.length > 0 && (
          <div className="mt-2 flex flex-wrap gap-2">
            {brandTags.map((tag) => <BrandNamingBadge key={tag.id} brandName={tag.tag_value} />)}
          </div>
        )}
      </div>

      {/* 元信息 */}
      <div className="flex flex-wrap items-center gap-3 text-2xs text-fg-muted">
        <time>{formatDate(article.published_at)}</time>
        <span className="h-3 w-px bg-border" />
        <span>采集于 {formatDate(article.collected_at)}</span>
        <span className="h-3 w-px bg-border" />
        <span className="uppercase text-fg-light">{article.original_language}</span>
        <span className="h-3 w-px bg-border" />
        <a href={article.original_url} target="_blank" rel="noopener noreferrer"
          className="inline-flex items-center gap-1 text-primary hover:underline">
          <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 6H5.25A2.25 2.25 0 003 8.25v10.5A2.25 2.25 0 005.25 21h10.5A2.25 2.25 0 0018 18.75V10.5m-10.5 6L21 3m0 0h-5.25M21 3v5.25" />
          </svg>
          查看原文
        </a>
      </div>

      {/* 原文内容区域 — 直接展示 */}
      <div className="rounded-lg border border-border bg-bg p-6">
        <div className="mb-3 flex items-center justify-between">
          <h3 className="text-[13px] font-medium text-fg-secondary">原文</h3>
          <span className="rounded-md bg-bg-hover px-2 py-0.5 text-2xs text-fg-muted uppercase">{article.original_language}</span>
        </div>

        {/* 英文原标题 */}
        <h4 className="text-[15px] font-medium leading-snug text-fg">{article.original_title}</h4>

        {/* 原文正文 */}
        {article.original_excerpt && (
          <div className="mt-4 text-[13px] leading-[1.8] text-fg-secondary whitespace-pre-line">
            {article.original_excerpt}
          </div>
        )}

        {!article.original_excerpt && (
          <p className="mt-4 text-[13px] text-fg-muted italic">原文内容将在采集时自动抓取</p>
        )}
      </div>
    </div>
  );
}
