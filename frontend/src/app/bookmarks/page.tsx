'use client';

import { useState, useEffect, useCallback } from 'react';
import * as Tabs from '@radix-ui/react-tabs';
import clsx from 'clsx';
import { api } from '@/lib/api';
import type { Article, PaginatedData } from '@/types';
import PageHeader from '@/components/layout/PageHeader';
import LoadingSpinner from '@/components/ui/LoadingSpinner';
import ErrorMessage from '@/components/ui/ErrorMessage';
import EmptyState from '@/components/ui/EmptyState';
import Pagination from '@/components/ui/Pagination';
import DateRangePicker from '@/components/ui/DateRangePicker';
import ArticleCard from '@/components/articles/ArticleCard';

const PAGE_SIZE = 20;

const CONTENT_TYPES = [
  '联名', '新品', '秀场', '广告', 'lookbook',
  '品牌动态', '快闪展览', '穿搭', '球鞋配饰', '行业趋势',
];

interface BookmarkFilters {
  brand?: string;
  content_type?: string;
  start_date?: string;
  end_date?: string;
  page: number;
  page_size: number;
}

export default function BookmarksPage() {
  const [activeTab, setActiveTab] = useState<'bookmarks' | 'topic-candidates'>('bookmarks');
  const [articles, setArticles] = useState<Article[]>([]);
  const [total, setTotal] = useState(0);
  const [filters, setFilters] = useState<BookmarkFilters>({ page: 1, page_size: PAGE_SIZE });
  const [brands, setBrands] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchBrands() {
      try {
        const res = await api.get<unknown>('/admin/brands', { page_size: '200' });
        const data = res as { items?: Array<{ name_en: string }> } | Array<{ name_en: string }>;
        if (Array.isArray(data)) setBrands(data.map((b) => b.name_en));
        else if (data && 'items' in data) setBrands(data.items!.map((b) => b.name_en));
      } catch { /* Non-critical */ }
    }
    fetchBrands();
  }, []);

  const fetchItems = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const endpoint = activeTab === 'bookmarks' ? '/bookmarks' : '/topic-candidates';
      const params: Record<string, string> = { page: String(filters.page), page_size: String(filters.page_size) };
      if (filters.brand) params.brand = filters.brand;
      if (filters.content_type) params.content_type = filters.content_type;
      if (filters.start_date) params.start_date = filters.start_date;
      if (filters.end_date) params.end_date = filters.end_date;

      const data = await api.get<PaginatedData<{ article?: Article; article_id: string }>>(endpoint, params);
      const items = data.items.map((item) => item.article).filter((a): a is Article => !!a);
      setArticles(items);
      setTotal(data.total);
    } catch {
      setError(activeTab === 'bookmarks' ? '加载收藏列表失败，请稍后重试' : '加载待选题列表失败，请稍后重试');
    } finally {
      setLoading(false);
    }
  }, [activeTab, filters]);

  useEffect(() => { fetchItems(); }, [fetchItems]);

  const handleTabChange = (value: string) => {
    setActiveTab(value as 'bookmarks' | 'topic-candidates');
    setFilters({ page: 1, page_size: PAGE_SIZE });
  };

  const handleToggleBookmark = useCallback(async (articleId: string) => {
    const article = articles.find((a) => a.id === articleId);
    if (!article) return;
    try {
      if (article.is_bookmarked) { await api.delete(`/bookmarks/${articleId}`); } else { await api.post('/bookmarks', { article_id: articleId }); }
      if (activeTab === 'bookmarks' && article.is_bookmarked) { fetchItems(); }
      else { setArticles((prev) => prev.map((a) => a.id === articleId ? { ...a, is_bookmarked: !a.is_bookmarked } : a)); }
    } catch { fetchItems(); }
  }, [articles, activeTab, fetchItems]);

  const handleToggleTopicCandidate = useCallback(async (articleId: string) => {
    const article = articles.find((a) => a.id === articleId);
    if (!article) return;
    try {
      if (article.is_topic_candidate) { await api.delete(`/topic-candidates/${articleId}`); } else { await api.post('/topic-candidates', { article_id: articleId }); }
      if (activeTab === 'topic-candidates' && article.is_topic_candidate) { fetchItems(); }
      else { setArticles((prev) => prev.map((a) => a.id === articleId ? { ...a, is_topic_candidate: !a.is_topic_candidate } : a)); }
    } catch { fetchItems(); }
  }, [articles, activeTab, fetchItems]);

  const handlePageChange = (page: number) => { setFilters((prev) => ({ ...prev, page })); window.scrollTo({ top: 0, behavior: 'smooth' }); };
  const handleDateChange = (start: string, end: string) => { setFilters((prev) => ({ ...prev, start_date: start || undefined, end_date: end || undefined, page: 1 })); };
  const clearFilters = () => { setFilters({ page: 1, page_size: PAGE_SIZE }); };
  const activeFilterCount = [filters.brand, filters.content_type, filters.start_date || filters.end_date].filter(Boolean).length;

  return (
    <div className="space-y-6 pb-12">
      <PageHeader title="收藏与待选题" breadcrumbs={[{ label: '首页', href: '/' }, { label: '收藏与待选题' }]} />

      <Tabs.Root value={activeTab} onValueChange={handleTabChange}>
        <Tabs.List className="flex items-center gap-0.5 rounded-lg border border-border bg-white p-0.5 w-fit">
          <Tabs.Trigger value="bookmarks" className={clsx('rounded-md px-3 py-1.5 text-[13px] font-medium transition-colors', 'data-[state=active]:bg-bg-active data-[state=active]:text-fg', 'data-[state=inactive]:text-fg-muted data-[state=inactive]:hover:text-fg-secondary')}>
            <span className="flex items-center gap-1.5">
              <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M17.593 3.322c1.1.128 1.907 1.077 1.907 2.185V21L12 17.25 4.5 21V5.507c0-1.108.806-2.057 1.907-2.185a48.507 48.507 0 0111.186 0z" /></svg>
              收藏
            </span>
          </Tabs.Trigger>
          <Tabs.Trigger value="topic-candidates" className={clsx('rounded-md px-3 py-1.5 text-[13px] font-medium transition-colors', 'data-[state=active]:bg-bg-active data-[state=active]:text-fg', 'data-[state=inactive]:text-fg-muted data-[state=inactive]:hover:text-fg-secondary')}>
            <span className="flex items-center gap-1.5">
              <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.455 2.456L21.75 6l-1.036.259a3.375 3.375 0 00-2.455 2.456z" /></svg>
              待选题
            </span>
          </Tabs.Trigger>
        </Tabs.List>

        <div className="mt-4 flex flex-wrap items-center gap-2">
          <select value={filters.brand || ''} onChange={(e) => setFilters((prev) => ({ ...prev, brand: e.target.value || undefined, page: 1 }))} className="h-8 rounded-lg border border-border bg-white px-3 text-[13px] text-fg-secondary hover:border-border-hover focus:border-primary/50 focus:outline-none focus:ring-1 focus:ring-primary/20">
            <option value="">全部品牌</option>
            {brands.map((brand) => <option key={brand} value={brand}>{brand}</option>)}
          </select>
          <select value={filters.content_type || ''} onChange={(e) => setFilters((prev) => ({ ...prev, content_type: e.target.value || undefined, page: 1 }))} className="h-8 rounded-lg border border-border bg-white px-3 text-[13px] text-fg-secondary hover:border-border-hover focus:border-primary/50 focus:outline-none focus:ring-1 focus:ring-primary/20">
            <option value="">全部类型</option>
            {CONTENT_TYPES.map((type) => <option key={type} value={type}>{type}</option>)}
          </select>
          <DateRangePicker startDate={filters.start_date || ''} endDate={filters.end_date || ''} onChange={handleDateChange} />
          {activeFilterCount > 0 && (
            <div className="flex items-center gap-2">
              <span className="inline-flex items-center gap-1 rounded-md bg-primary-bg px-2 py-1 text-2xs font-medium text-primary">{activeFilterCount} 个筛选</span>
              <button onClick={clearFilters} className="text-2xs text-fg-muted transition-colors hover:text-fg">清除全部</button>
            </div>
          )}
        </div>

        <Tabs.Content value="bookmarks" className="mt-6">
          <TabContent articles={articles} total={total} loading={loading} error={error} filters={filters} onRetry={fetchItems} onToggleBookmark={handleToggleBookmark} onToggleTopicCandidate={handleToggleTopicCandidate} onPageChange={handlePageChange} emptyTitle="暂无收藏" emptyDescription="您还没有收藏任何资讯，在资讯列表中点击收藏按钮即可添加" />
        </Tabs.Content>
        <Tabs.Content value="topic-candidates" className="mt-6">
          <TabContent articles={articles} total={total} loading={loading} error={error} filters={filters} onRetry={fetchItems} onToggleBookmark={handleToggleBookmark} onToggleTopicCandidate={handleToggleTopicCandidate} onPageChange={handlePageChange} emptyTitle="暂无待选题" emptyDescription="您还没有标记任何待选题，在资讯列表中点击待选题按钮即可添加" />
        </Tabs.Content>
      </Tabs.Root>
    </div>
  );
}

function TabContent({ articles, total, loading, error, filters, onRetry, onToggleBookmark, onToggleTopicCandidate, onPageChange, emptyTitle, emptyDescription }: {
  articles: Article[]; total: number; loading: boolean; error: string | null; filters: BookmarkFilters; onRetry: () => void; onToggleBookmark: (id: string) => void; onToggleTopicCandidate: (id: string) => void; onPageChange: (page: number) => void; emptyTitle: string; emptyDescription: string;
}) {
  if (loading) return <div className="flex min-h-[40vh] items-center justify-center"><LoadingSpinner size="lg" label="加载中…" /></div>;
  if (error) return <ErrorMessage message={error} onRetry={onRetry} />;
  if (articles.length === 0) return <EmptyState title={emptyTitle} description={emptyDescription} />;

  return (
    <>
      <p className="mb-3 text-2xs text-fg-muted">共 <span className="font-medium text-fg-secondary">{total}</span> 条</p>
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {articles.map((article) => (
          <ArticleCard key={article.id} article={article} onToggleBookmark={onToggleBookmark} onToggleTopicCandidate={onToggleTopicCandidate} />
        ))}
      </div>
      <Pagination page={filters.page} total={total} pageSize={filters.page_size} onPageChange={onPageChange} className="mt-6" />
    </>
  );
}
