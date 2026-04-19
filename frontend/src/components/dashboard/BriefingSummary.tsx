'use client';

import Link from 'next/link';
import type { DailyBriefing } from '@/types';

export default function BriefingSummary({ briefing }: { briefing: DailyBriefing | null }) {
  if (!briefing) return (
    <section className="rounded-lg border border-border bg-white p-6 shadow-card">
      <h2 className="text-[15px] font-semibold text-fg">今日简报</h2>
      <p className="mt-2 text-[13px] text-fg-muted">今日简报尚未生成</p>
    </section>
  );

  return (
    <section>
      <Link href={`/briefings/${briefing.id}`} className="group block">
        <div className="rounded-lg border border-border bg-white p-6 shadow-card transition-shadow hover:shadow-card-hover">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary-bg">
                <svg className="h-5 w-5 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h3.75M9 15h3.75M9 18h3.75m3 .75H18a2.25 2.25 0 002.25-2.25V6.108c0-1.135-.845-2.098-1.976-2.192a48.424 48.424 0 00-1.123-.08m-5.801 0c-.065.21-.1.433-.1.664 0 .414.336.75.75.75h4.5a.75.75 0 00.75-.75 2.25 2.25 0 00-.1-.664m-5.8 0A2.251 2.251 0 0113.5 2.25H15a2.25 2.25 0 012.15 1.586m-5.8 0c-.376.023-.75.05-1.124.08C9.095 4.01 8.25 4.973 8.25 6.108V8.25m0 0H4.875c-.621 0-1.125.504-1.125 1.125v11.25c0 .621.504 1.125 1.125 1.125h9.75c.621 0 1.125-.504 1.125-1.125V9.375c0-.621-.504-1.125-1.125-1.125H8.25z" />
                </svg>
              </div>
              <div>
                <h2 className="text-[15px] font-semibold text-fg">今日简报</h2>
                <p className="text-2xs text-fg-muted">{briefing.briefing_date}</p>
              </div>
            </div>
            <span className="text-[13px] text-fg-muted transition-colors group-hover:text-primary">查看完整简报 →</span>
          </div>
          {briefing.content?.summary && (
            <p className="mt-4 line-clamp-2 text-[13px] leading-relaxed text-fg-secondary">{briefing.content.summary}</p>
          )}
          {briefing.content?.trends?.length > 0 && (
            <div className="mt-3 flex flex-wrap gap-1.5">
              {briefing.content.trends.slice(0, 4).map((t, i) => (
                <span key={i} className="rounded-md bg-bg-hover px-2 py-0.5 text-2xs text-fg-secondary">{t}</span>
              ))}
            </div>
          )}
        </div>
      </Link>
    </section>
  );
}
