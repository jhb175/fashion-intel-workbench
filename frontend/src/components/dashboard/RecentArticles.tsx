'use client';

import Link from 'next/link';
import type { Article } from '@/types';
import TagBadge from '@/components/ui/TagBadge';

function relTime(d: string) {
  const ms = Date.now() - new Date(d).getTime();
  const m = Math.floor(ms / 60000), h = Math.floor(ms / 3600000), dy = Math.floor(ms / 86400000);
  if (m < 1) return '刚刚';
  if (m < 60) return `${m}分钟前`;
  if (h < 24) return `${h}小时前`;
  if (dy < 7) return `${dy}天前`;
  return new Date(d).toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' });
}

export default function RecentArticles({ articles }: { articles: Article[] }) {
  if (!articles.length) return (
    <section>
      <h2 className="text-[15px] font-semibold text-fg">最近资讯</h2>
      <p className="mt-3 text-[13px] text-fg-muted">暂无资讯</p>
    </section>
  );

  return (
    <section>
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-[15px] font-semibold text-fg">最近资讯</h2>
        <Link href="/articles" className="text-[13px] text-fg-muted hover:text-primary transition-colors">查看全部 →</Link>
      </div>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {articles.map((a) => (
          <Link key={a.id} href={`/articles/${a.id}`} className="group block">
            <div className="flex h-full flex-col rounded-lg border border-border bg-white p-5 shadow-card transition-shadow hover:shadow-card-hover">
              <h3 className="line-clamp-2 text-[14px] font-medium leading-snug text-fg group-hover:text-primary transition-colors">
                {a.chinese_summary || a.original_title}
              </h3>
              <p className="mt-1.5 line-clamp-1 text-2xs text-fg-muted italic">{a.original_title}</p>
              {a.tags?.length > 0 && (
                <div className="mt-3 flex flex-wrap gap-1.5">
                  {a.tags.slice(0, 3).map((t) => <TagBadge key={t.id} label={t.tag_value} variant={t.tag_type} />)}
                </div>
              )}
              <div className="mt-auto pt-3">
                <time className="text-2xs text-fg-light">{relTime(a.published_at || a.collected_at)}</time>
              </div>
            </div>
          </Link>
        ))}
      </div>
    </section>
  );
}
