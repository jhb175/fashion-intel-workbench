'use client';

import Link from 'next/link';
import type { DailyBriefing } from '@/types';
import TagBadge from '@/components/ui/TagBadge';

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString('zh-CN', { year: 'numeric', month: 'long', day: 'numeric', weekday: 'long' });
}

export default function BriefingDetail({ briefing }: { briefing: DailyBriefing }) {
  const { content } = briefing;

  return (
    <div className="space-y-6">
      {/* Header info */}
      <div className="flex items-center gap-3">
        <time className="text-[13px] text-fg-secondary">{formatDate(briefing.briefing_date)}</time>
        {briefing.has_new_articles ? (
          <span className="inline-flex items-center gap-1 rounded-md border border-emerald-200 bg-emerald-50 px-1.5 py-0.5 text-2xs font-medium text-emerald-600">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />有新资讯
          </span>
        ) : (
          <span className="inline-flex items-center rounded-md border border-border bg-bg-hover px-1.5 py-0.5 text-2xs font-medium text-fg-light">无新增资讯</span>
        )}
      </div>

      {/* Summary */}
      {content?.summary && (
        <section className="rounded-lg border border-border bg-white p-5 shadow-card">
          <h2 className="mb-2 text-[14px] font-medium text-fg">今日概述</h2>
          <p className="text-[13px] leading-relaxed text-fg-secondary">{content.summary}</p>
        </section>
      )}

      {/* Monitor group sections */}
      {content?.sections && content.sections.length > 0 && (
        <div className="space-y-4">
          <h2 className="text-[14px] font-medium text-fg">重点资讯</h2>
          {content.sections.map((section) => (
            <section key={section.monitor_group} className="rounded-lg border border-border bg-white p-5 shadow-card">
              <h3 className="mb-3 flex items-center gap-2 text-[13px] font-medium text-fg">
                <span className="inline-flex h-5 w-5 items-center justify-center rounded-md bg-blue-50 text-2xs text-blue-600">
                  {section.highlights.length}
                </span>
                {section.monitor_group}
              </h3>
              <div className="space-y-3">
                {section.highlights.map((highlight) => (
                  <div key={highlight.article_id} className="group rounded-md border border-border bg-bg-hover p-3 transition-colors hover:border-border-hover">
                    <Link href={`/articles/${highlight.article_id}`} className="block">
                      <h4 className="text-[13px] font-medium text-fg transition-colors group-hover:text-primary">{highlight.title}</h4>
                      {highlight.summary && <p className="mt-1 text-2xs leading-relaxed text-fg-muted">{highlight.summary}</p>}
                    </Link>
                  </div>
                ))}
              </div>
            </section>
          ))}
        </div>
      )}

      {/* Trends */}
      {content?.trends && content.trends.length > 0 && (
        <section className="rounded-lg border border-amber-200 bg-amber-50 p-5">
          <h2 className="mb-2 text-[14px] font-medium text-fg">趋势热点</h2>
          <div className="flex flex-wrap gap-1.5">
            {content.trends.map((trend, i) => <TagBadge key={i} label={trend} variant="keyword" />)}
          </div>
        </section>
      )}

      {/* Follow-up suggestions */}
      {content?.follow_up_suggestions && content.follow_up_suggestions.length > 0 && (
        <section className="rounded-lg border border-purple-200 bg-purple-50 p-5">
          <h2 className="mb-2 text-[14px] font-medium text-fg">跟进建议</h2>
          <ul className="space-y-2">
            {content.follow_up_suggestions.map((suggestion, i) => (
              <li key={i} className="flex items-start gap-2 text-[13px] text-fg-secondary">
                <svg className="mt-0.5 h-3.5 w-3.5 flex-shrink-0 text-purple-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
                </svg>
                <span>{suggestion}</span>
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}
