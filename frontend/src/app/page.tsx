'use client';

import { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import { api } from '@/lib/api';
import type { DashboardOverview, Article, DailyBriefing, PaginatedData } from '@/types';
import TagBadge from '@/components/ui/TagBadge';

/* ── Mock 数据（后端未启动时展示） ── */
const MOCK_OVERVIEW: DashboardOverview = {
  today_new_articles: 47,
  pending_count: 12,
  bookmark_count: 86,
  topic_candidate_count: 23,
  group_distribution: { Luxury: 18, Sports: 14, Outdoor: 9, 'Rap/Culture': 6 },
};

const MOCK_ARTICLES: Article[] = [
  { id: '1', source_id: 's1', original_title: 'Louis Vuitton x Pharrell: A New Chapter in Luxury Streetwear', original_url: '#', original_language: 'en', chinese_summary: 'Louis Vuitton 与 Pharrell Williams 联名系列正式发布，将街头文化与高级时装深度融合，标志着奢侈品牌拥抱潮流文化的新篇章。', collected_at: new Date().toISOString(), published_at: new Date(Date.now() - 3600000).toISOString(), processing_status: 'processed', tags: [{ id: 't1', article_id: '1', tag_type: 'brand', tag_value: 'Louis Vuitton', is_auto: true, created_at: '' }, { id: 't2', article_id: '1', tag_type: 'content_type', tag_value: '联名', is_auto: true, created_at: '' }], created_at: '', updated_at: '' },
  { id: '2', source_id: 's1', original_title: 'Nike Air Max Dn Drops in Three New Colorways', original_url: '#', original_language: 'en', chinese_summary: 'Nike Air Max Dn 推出三款全新配色，延续 Dynamic Air 技术革新，定价 ¥1,099，将于下周全球发售。', collected_at: new Date().toISOString(), published_at: new Date(Date.now() - 7200000).toISOString(), processing_status: 'processed', tags: [{ id: 't3', article_id: '2', tag_type: 'brand', tag_value: 'Nike', is_auto: true, created_at: '' }, { id: 't4', article_id: '2', tag_type: 'content_type', tag_value: '新品', is_auto: true, created_at: '' }], created_at: '', updated_at: '' },
  { id: '3', source_id: 's1', original_title: "Arc'teryx Opens Flagship Store in Shanghai", original_url: '#', original_language: 'en', chinese_summary: "始祖鸟在上海开设全球最大旗舰店，占地 800 平方米，融合户外体验空间与零售概念，进一步巩固其在中国市场的高端户外定位。", collected_at: new Date().toISOString(), published_at: new Date(Date.now() - 10800000).toISOString(), processing_status: 'processed', tags: [{ id: 't5', article_id: '3', tag_type: 'brand', tag_value: "Arc'teryx", is_auto: true, created_at: '' }, { id: 't6', article_id: '3', tag_type: 'content_type', tag_value: '品牌动态', is_auto: true, created_at: '' }], created_at: '', updated_at: '' },
  { id: '4', source_id: 's1', original_title: 'Supreme x The North Face FW25 Collection Revealed', original_url: '#', original_language: 'en', chinese_summary: 'Supreme 与 The North Face 2025 秋冬联名系列曝光，包含冲锋衣、羽绒服和配件，延续双方长达 18 年的经典合作。', collected_at: new Date().toISOString(), published_at: new Date(Date.now() - 14400000).toISOString(), processing_status: 'processed', tags: [{ id: 't7', article_id: '4', tag_type: 'brand', tag_value: 'Supreme', is_auto: true, created_at: '' }, { id: 't8', article_id: '4', tag_type: 'content_type', tag_value: '联名', is_auto: true, created_at: '' }], created_at: '', updated_at: '' },
  { id: '5', source_id: 's1', original_title: 'Balenciaga Spring 2026 Runway Show in Paris', original_url: '#', original_language: 'en', chinese_summary: 'Balenciaga 2026 春夏系列在巴黎发布，Demna 以解构主义手法重新诠释经典廓形，秀场设计引发行业热议。', collected_at: new Date().toISOString(), published_at: new Date(Date.now() - 18000000).toISOString(), processing_status: 'processed', tags: [{ id: 't9', article_id: '5', tag_type: 'brand', tag_value: 'Balenciaga', is_auto: true, created_at: '' }, { id: 't10', article_id: '5', tag_type: 'content_type', tag_value: '秀场', is_auto: true, created_at: '' }], created_at: '', updated_at: '' },
  { id: '6', source_id: 's1', original_title: 'adidas and Bad Bunny Unveil New Campus Colorway', original_url: '#', original_language: 'en', chinese_summary: 'adidas 与 Bad Bunny 合作推出全新 Campus 配色，以波多黎各文化为灵感，限量发售引发抢购热潮。', collected_at: new Date().toISOString(), published_at: new Date(Date.now() - 21600000).toISOString(), processing_status: 'processed', tags: [{ id: 't11', article_id: '6', tag_type: 'brand', tag_value: 'adidas', is_auto: true, created_at: '' }, { id: 't12', article_id: '6', tag_type: 'content_type', tag_value: '球鞋配饰', is_auto: true, created_at: '' }], created_at: '', updated_at: '' },
];

const MOCK_TAGS: Record<string, { tag_value: string; count: number }[]> = {
  Luxury: [{ tag_value: '联名', count: 12 }, { tag_value: '秀场', count: 9 }, { tag_value: '新品', count: 7 }, { tag_value: '广告', count: 5 }],
  Sports: [{ tag_value: '球鞋', count: 15 }, { tag_value: '联名', count: 8 }, { tag_value: '新品', count: 6 }, { tag_value: '复刻', count: 4 }],
  Outdoor: [{ tag_value: '品牌动态', count: 6 }, { tag_value: '联名', count: 4 }, { tag_value: '机能', count: 3 }],
  'Rap/Culture': [{ tag_value: '街头', count: 8 }, { tag_value: '限量', count: 5 }, { tag_value: '联名', count: 4 }],
};

function getGreeting() {
  const h = new Date().getHours();
  if (h < 6) return '夜深了';
  if (h < 12) return '早上好';
  if (h < 14) return '中午好';
  if (h < 18) return '下午好';
  return '晚上好';
}

function formatDate() {
  return new Date().toLocaleDateString('zh-CN', { year: 'numeric', month: 'long', day: 'numeric', weekday: 'long' });
}

function relTime(d: string) {
  const ms = Date.now() - new Date(d).getTime();
  const m = Math.floor(ms / 60000), h = Math.floor(ms / 3600000);
  if (m < 1) return '刚刚';
  if (m < 60) return `${m}分钟前`;
  if (h < 24) return `${h}小时前`;
  return new Date(d).toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' });
}

const statItems = [
  { key: 'today_new_articles' as const, label: '今日新增', icon: '📰' },
  { key: 'pending_count' as const, label: '待处理', icon: '⏳' },
  { key: 'bookmark_count' as const, label: '已收藏', icon: '🔖' },
  { key: 'topic_candidate_count' as const, label: '待选题', icon: '✨' },
];

export default function DashboardPage() {
  const [overview, setOverview] = useState<DashboardOverview>(MOCK_OVERVIEW);
  const [articles, setArticles] = useState<Article[]>(MOCK_ARTICLES);
  const [tags, setTags] = useState<Record<string, { tag_value: string; count: number }[]>>(MOCK_TAGS);
  const [briefing, setBriefing] = useState<DailyBriefing | null>(null);
  const [isLive, setIsLive] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      const [o, a, t, b] = await Promise.allSettled([
        api.get<DashboardOverview>('/dashboard/overview'),
        api.get<Article[]>('/dashboard/recent-articles'),
        api.get<Record<string, { tag_value: string; count: number }[]>>('/dashboard/trending-tags'),
        api.get<PaginatedData<DailyBriefing>>('/briefings', { page: '1', page_size: '1' }),
      ]);
      if (o.status === 'fulfilled') { setOverview(o.value); setIsLive(true); }
      if (a.status === 'fulfilled') setArticles(a.value);
      if (t.status === 'fulfilled') setTags(t.value);
      if (b.status === 'fulfilled' && b.value.items.length) setBriefing(b.value.items[0]);
    } catch { /* use mock data */ }
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  return (
    <div className="space-y-8 pb-12">
      {/* ── 顶部 Hero ── */}
      <section className="relative overflow-hidden rounded-2xl border border-border bg-gradient-to-br from-indigo-50 via-white to-purple-50/50 px-8 py-8 lg:py-10">
        {/* 装饰 */}
        <div className="pointer-events-none absolute -right-20 -top-20 h-56 w-56 rounded-full bg-indigo-200/30 blur-3xl" />
        <div className="pointer-events-none absolute -bottom-16 -left-16 h-40 w-40 rounded-full bg-purple-200/20 blur-3xl" />
        <div className="pointer-events-none absolute right-1/3 top-1/4 h-2 w-2 rounded-full bg-indigo-400/40" />
        <div className="pointer-events-none absolute right-1/4 top-1/2 h-1.5 w-1.5 rounded-full bg-purple-400/30" />

        <div className="relative flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-[13px] text-fg-muted">{formatDate()}</p>
            <h1 className="mt-1.5 text-[28px] font-bold leading-tight tracking-tight text-fg">
              {getGreeting()}，<span className="bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">潮流编辑</span>
            </h1>
            <p className="mt-2 max-w-md text-[14px] leading-relaxed text-fg-secondary">
              全球时尚潮流资讯尽在掌握，今日有
              <span className="mx-1 font-semibold text-primary">{overview.today_new_articles}</span>
              条新资讯等待查阅
            </p>
            {!isLive && (
              <p className="mt-2 inline-flex items-center gap-1.5 rounded-full bg-amber-50 border border-amber-200/60 px-2.5 py-1 text-2xs text-amber-700">
                <span className="h-1.5 w-1.5 rounded-full bg-amber-400" />
                演示模式 · 后端未连接
              </p>
            )}
          </div>

          {/* 统计卡片 */}
          <div className="flex gap-3">
            {statItems.map((s) => (
              <div key={s.key} className="min-w-[96px] rounded-xl border border-border bg-white px-4 py-3 text-center shadow-card transition-shadow hover:shadow-card-hover">
                <p className="text-[22px] font-bold tracking-tight text-fg">{overview[s.key]}</p>
                <p className="mt-0.5 text-2xs text-fg-muted">{s.label}</p>
              </div>
            ))}
          </div>
        </div>

        {/* 监控组分布 */}
        {Object.keys(overview.group_distribution).length > 0 && (
          <div className="relative mt-6 flex flex-wrap items-center gap-x-5 gap-y-1.5 border-t border-border/50 pt-4">
            <span className="text-2xs font-medium text-fg-muted">监控组</span>
            {Object.entries(overview.group_distribution).map(([group, count]) => (
              <span key={group} className="flex items-center gap-1.5 text-[13px] text-fg-secondary">
                <span className="h-1.5 w-1.5 rounded-full bg-primary/50" />
                {group}
                <span className="font-semibold text-fg">{count}</span>
              </span>
            ))}
          </div>
        )}
      </section>

      {/* ── 今日简报 ── */}
      {briefing ? (
        <section>
          <Link href={`/briefings/${briefing.id}`} className="group block">
            <div className="rounded-xl border border-border bg-white p-6 shadow-card transition-shadow hover:shadow-card-hover">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary-bg">
                    <span className="text-base">📋</span>
                  </div>
                  <div>
                    <h2 className="text-[15px] font-semibold text-fg">今日简报</h2>
                    <p className="text-2xs text-fg-muted">{briefing.briefing_date}</p>
                  </div>
                </div>
                <span className="text-[13px] text-fg-muted group-hover:text-primary transition-colors">查看 →</span>
              </div>
              {briefing.content?.summary && <p className="mt-3 line-clamp-2 text-[13px] text-fg-secondary">{briefing.content.summary}</p>}
            </div>
          </Link>
        </section>
      ) : (
        <section className="rounded-xl border border-border bg-white p-6 shadow-card">
          <h2 className="text-[15px] font-semibold text-fg">今日简报</h2>
          <p className="mt-2 text-[13px] text-fg-muted">简报将在后端启动后自动生成</p>
        </section>
      )}

      {/* ── 最近资讯 ── */}
      <section>
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-[15px] font-semibold text-fg">最近资讯</h2>
          <Link href="/articles" className="text-[13px] text-fg-muted hover:text-primary transition-colors">查看全部 →</Link>
        </div>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {articles.map((a) => (
            <Link key={a.id} href={`/articles/${a.id}`} className="group block">
              <div className="flex h-full flex-col rounded-xl border border-border bg-white p-5 shadow-card transition-all hover:shadow-card-hover hover:border-border-hover">
                <h3 className="line-clamp-2 text-[14px] font-medium leading-snug text-fg group-hover:text-primary transition-colors">
                  {a.chinese_summary || a.original_title}
                </h3>
                <p className="mt-1.5 line-clamp-1 text-2xs text-fg-light italic">{a.original_title}</p>
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

      {/* ── 热门标签 ── */}
      <section>
        <h2 className="mb-4 text-[15px] font-semibold text-fg">热门标签</h2>
        <div className="grid gap-4 sm:grid-cols-2">
          {Object.entries(tags).map(([name, items]) => {
            const max = Math.max(...items.map((t) => t.count), 1);
            return (
              <div key={name} className="rounded-xl border border-border bg-white p-5 shadow-card">
                <h3 className="mb-3 flex items-center gap-2 text-[13px] font-medium text-fg-secondary">
                  <span className="h-2 w-2 rounded-full bg-gradient-to-r from-primary to-purple-500" />{name}
                </h3>
                <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1.5">
                  {items.map((t, i) => (
                    <span key={i} className="text-fg-secondary hover:text-primary transition-colors cursor-default"
                      style={{
                        fontSize: t.count / max > 0.6 ? '13px' : '11px',
                        fontWeight: t.count / max > 0.6 ? 600 : 400,
                        opacity: 0.5 + 0.5 * (t.count / max),
                      }}>
                      {t.tag_value}<span className="ml-0.5 text-[10px] text-fg-light">{t.count}</span>
                    </span>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      </section>
    </div>
  );
}
