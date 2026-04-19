'use client';

import type { DashboardOverview } from '@/types';

/**
 * 统计概览组件（备用）
 * 主仪表盘已将统计数据内联到顶部 Hero 区域，
 * 此组件保留供其他页面复用。
 */
const statItems = (d: DashboardOverview) => [
  { label: '今日新增', value: d.today_new_articles },
  { label: '待处理', value: d.pending_count },
  { label: '已收藏', value: d.bookmark_count },
  { label: '待选题', value: d.topic_candidate_count },
];

export default function StatsOverview({ data }: { data: DashboardOverview }) {
  return (
    <section className="grid grid-cols-2 gap-3 lg:grid-cols-4">
      {statItems(data).map((s) => (
        <div key={s.label} className="rounded-lg border border-border bg-white px-4 py-3.5 shadow-card">
          <p className="text-2xs font-medium text-fg-muted uppercase tracking-wider">{s.label}</p>
          <p className="mt-1 text-2xl font-semibold tracking-tight text-fg">{s.value.toLocaleString()}</p>
        </div>
      ))}
    </section>
  );
}
