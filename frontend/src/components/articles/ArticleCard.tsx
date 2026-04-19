'use client';

import Link from 'next/link';
import clsx from 'clsx';
import type { Article } from '@/types';
import TagBadge from '@/components/ui/TagBadge';

interface ArticleCardProps {
  article: Article;
  onToggleBookmark: (articleId: string) => void;
  onToggleTopicCandidate: (articleId: string) => void;
}

function formatRelativeTime(dateStr: string): string {
  const date = new Date(dateStr);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMin = Math.floor(diffMs / 60000);
  const diffHour = Math.floor(diffMs / 3600000);
  const diffDay = Math.floor(diffMs / 86400000);

  if (diffMin < 1) return '刚刚';
  if (diffMin < 60) return `${diffMin} 分钟前`;
  if (diffHour < 24) return `${diffHour} 小时前`;
  if (diffDay < 7) return `${diffDay} 天前`;
  return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' });
}

export default function ArticleCard({
  article,
  onToggleBookmark,
  onToggleTopicCandidate,
}: ArticleCardProps) {
  const timeStr = article.published_at
    ? formatRelativeTime(article.published_at)
    : formatRelativeTime(article.collected_at);

  return (
    <article
      className={clsx(
        'group relative flex flex-col rounded-lg border bg-white p-4 shadow-card transition-shadow hover:shadow-card-hover',
        article.is_bookmarked || article.is_topic_candidate
          ? 'border-primary/20'
          : 'border-border',
      )}
    >
      {/* Visual marks */}
      {(article.is_bookmarked || article.is_topic_candidate) && (
        <div className="absolute right-3 top-3 flex items-center gap-1">
          {article.is_bookmarked && (
            <span className="flex h-5 w-5 items-center justify-center rounded-md bg-amber-50" title="已收藏">
              <svg className="h-3 w-3 text-amber-500" fill="currentColor" viewBox="0 0 24 24">
                <path d="M5 2h14a1 1 0 011 1v19.143a.5.5 0 01-.766.424L12 18.03l-7.234 4.536A.5.5 0 014 22.143V3a1 1 0 011-1z" />
              </svg>
            </span>
          )}
          {article.is_topic_candidate && (
            <span className="flex h-5 w-5 items-center justify-center rounded-md bg-purple-50" title="待选题">
              <svg className="h-3 w-3 text-purple-500" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 2l2.09 6.26L20.18 9l-5.09 3.74L16.18 19 12 15.27 7.82 19l1.09-6.26L3.82 9l6.09-.74L12 2z" />
              </svg>
            </span>
          )}
        </div>
      )}

      {/* Chinese summary */}
      <Link href={`/articles/${article.id}`} className="block flex-1">
        <h3 className="line-clamp-3 text-[13px] font-medium leading-relaxed text-fg transition-colors group-hover:text-primary">
          {article.chinese_summary || article.original_title}
        </h3>
        <p className="mt-1.5 line-clamp-1 text-2xs text-fg-muted italic">
          {article.original_title}
        </p>
      </Link>

      {/* Tags */}
      {article.tags.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-1">
          {article.tags.slice(0, 4).map((tag) => (
            <TagBadge key={tag.id} label={tag.tag_value} variant={tag.tag_type} />
          ))}
          {article.tags.length > 4 && (
            <span className="inline-flex items-center text-2xs text-fg-light">+{article.tags.length - 4}</span>
          )}
        </div>
      )}

      {/* Footer */}
      <div className="mt-3 flex items-center justify-between border-t border-border pt-3">
        <time className="text-2xs text-fg-light">{timeStr}</time>
        <div className="flex items-center gap-1">
          <button
            onClick={(e) => { e.preventDefault(); onToggleBookmark(article.id); }}
            className={clsx(
              'rounded-md p-1.5 transition-colors',
              article.is_bookmarked ? 'text-amber-500 hover:bg-amber-50' : 'text-fg-light hover:bg-bg-hover hover:text-fg-secondary',
            )}
            title={article.is_bookmarked ? '取消收藏' : '收藏'}
            aria-label={article.is_bookmarked ? '取消收藏' : '收藏'}
          >
            <svg className="h-3.5 w-3.5" fill={article.is_bookmarked ? 'currentColor' : 'none'} viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M17.593 3.322c1.1.128 1.907 1.077 1.907 2.185V21L12 17.25 4.5 21V5.507c0-1.108.806-2.057 1.907-2.185a48.507 48.507 0 0111.186 0z" />
            </svg>
          </button>
          <button
            onClick={(e) => { e.preventDefault(); onToggleTopicCandidate(article.id); }}
            className={clsx(
              'rounded-md p-1.5 transition-colors',
              article.is_topic_candidate ? 'text-purple-500 hover:bg-purple-50' : 'text-fg-light hover:bg-bg-hover hover:text-fg-secondary',
            )}
            title={article.is_topic_candidate ? '取消待选题' : '标记待选题'}
            aria-label={article.is_topic_candidate ? '取消待选题' : '标记待选题'}
          >
            <svg className="h-3.5 w-3.5" fill={article.is_topic_candidate ? 'currentColor' : 'none'} viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.455 2.456L21.75 6l-1.036.259a3.375 3.375 0 00-2.455 2.456z" />
            </svg>
          </button>
        </div>
      </div>
    </article>
  );
}
