'use client';

import Link from 'next/link';
import type { DailyBriefing } from '@/types';
import EmptyState from '@/components/ui/EmptyState';

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString('zh-CN', { year: 'numeric', month: 'long', day: 'numeric', weekday: 'long' });
}

export default function BriefingList({ briefings }: { briefings: DailyBriefing[] }) {
  if (briefings.length === 0) {
    return <EmptyState title="暂无简报" description="系统尚未生成任何每日简报，请点击上方按钮手动生成" />;
  }

  return (
    <div className="space-y-3">
      {briefings.map((briefing) => (
        <Link key={briefing.id} href={`/briefings/${briefing.id}`} className="block">
          <article className="group rounded-lg border border-border bg-white p-5 shadow-card transition-shadow hover:shadow-card-hover">
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <h3 className="text-[14px] font-medium text-fg group-hover:text-primary transition-colors">
                    {formatDate(briefing.briefing_date)}
                  </h3>
                  {briefing.has_new_articles ? (
                    <span className="inline-flex items-center gap-1 rounded-md border border-emerald-200 bg-emerald-50 px-1.5 py-0.5 text-2xs font-medium text-emerald-600">
                      <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />有新资讯
                    </span>
                  ) : (
                    <span className="inline-flex items-center rounded-md border border-border bg-bg-hover px-1.5 py-0.5 text-2xs font-medium text-fg-light">无新增</span>
                  )}
                </div>
                {briefing.content?.summary && (
                  <p className="mt-1.5 line-clamp-2 text-[13px] leading-relaxed text-fg-secondary">{briefing.content.summary}</p>
                )}
                {briefing.content?.sections && briefing.content.sections.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-1.5">
                    {briefing.content.sections.map((section) => (
                      <span key={section.monitor_group} className="inline-flex items-center gap-1 rounded-md border border-blue-200 bg-blue-50 px-1.5 py-0.5 text-2xs font-medium text-blue-600">
                        {section.monitor_group}<span className="text-blue-400">·</span><span>{section.highlights.length}</span>
                      </span>
                    ))}
                  </div>
                )}
              </div>
              <svg className="mt-1 h-4 w-4 flex-shrink-0 text-fg-light transition-colors group-hover:text-fg-secondary" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
              </svg>
            </div>
          </article>
        </Link>
      ))}
    </div>
  );
}
