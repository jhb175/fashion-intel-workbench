'use client';

import { useState, useEffect, useCallback } from 'react';
import { api } from '@/lib/api';
import type { Article, ArticleFilters as FiltersType, PaginatedData } from '@/types';
import PageHeader from '@/components/layout/PageHeader';
import LoadingSpinner from '@/components/ui/LoadingSpinner';
import ErrorMessage from '@/components/ui/ErrorMessage';
import Pagination from '@/components/ui/Pagination';
import ArticleFilters from '@/components/articles/ArticleFilters';
import ArticleList from '@/components/articles/ArticleList';

const PAGE_SIZE = 20;

interface MonitorGroupOption {
  name: string;
  display_name: string;
}

export default function ArticlesPage() {
  const [articles, setArticles] = useState<Article[]>([]);
  const [total, setTotal] = useState(0);
  const [filters, setFilters] = useState<FiltersType>({
    page: 1,
    page_size: PAGE_SIZE,
    status: 'processed',
  });

  const [brands, setBrands] = useState<string[]>([]);
  const [monitorGroups, setMonitorGroups] = useState<MonitorGroupOption[]>([]);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchFilterOptions() {
      try {
        const [brandsRes, groupsRes] = await Promise.allSettled([
          api.get<Array<{ name_en: string }>>('/admin/brands', { page_size: '200' })
            .then((res: unknown) => {
              const data = res as { items?: Array<{ name_en: string }> } | Array<{ name_en: string }>;
              if (Array.isArray(data)) return data.map((b) => b.name_en);
              if (data && 'items' in data) return data.items!.map((b) => b.name_en);
              return [];
            }),
          api.get<MonitorGroupOption[]>('/admin/monitor-groups')
            .then((res: unknown) => {
              const data = res as { items?: MonitorGroupOption[] } | MonitorGroupOption[];
              if (Array.isArray(data)) return data;
              if (data && 'items' in data) return data.items!;
              return [];
            }),
        ]);
        if (brandsRes.status === 'fulfilled') setBrands(brandsRes.value);
        if (groupsRes.status === 'fulfilled') setMonitorGroups(groupsRes.value);
      } catch { /* Non-critical */ }
    }
    fetchFilterOptions();
  }, []);

  const fetchArticles = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params: Record<string, string> = {
        page: String(filters.page || 1),
        page_size: String(filters.page_size || PAGE_SIZE),
      };
      if (filters.brand) params.brand = filters.brand;
      if (filters.monitor_group) params.monitor_group = filters.monitor_group;
      if (filters.content_type) params.content_type = filters.content_type;
      if (filters.start_date) params.start_date = filters.start_date;
      if (filters.end_date) params.end_date = filters.end_date;
      if (filters.keyword) params.keyword = filters.keyword;
      if (filters.status) params.status = filters.status;

      const data = await api.get<PaginatedData<Article>>('/articles', params);
      setArticles(data.items);
      setTotal(data.total);
    } catch {
      setError('加载资讯列表失败，请稍后重试');
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => { fetchArticles(); }, [fetchArticles]);

  const handleToggleBookmark = useCallback(
    async (articleId: string) => {
      const article = articles.find((a) => a.id === articleId);
      if (!article) return;
      try {
        if (article.is_bookmarked) {
          await api.delete(`/bookmarks/${articleId}`);
        } else {
          await api.post('/bookmarks', { article_id: articleId });
        }
        setArticles((prev) =>
          prev.map((a) => a.id === articleId ? { ...a, is_bookmarked: !a.is_bookmarked } : a),
        );
      } catch { fetchArticles(); }
    },
    [articles, fetchArticles],
  );

  const handleToggleTopicCandidate = useCallback(
    async (articleId: string) => {
      const article = articles.find((a) => a.id === articleId);
      if (!article) return;
      try {
        if (article.is_topic_candidate) {
          await api.delete(`/topic-candidates/${articleId}`);
        } else {
          await api.post('/topic-candidates', { article_id: articleId });
        }
        setArticles((prev) =>
          prev.map((a) => a.id === articleId ? { ...a, is_topic_candidate: !a.is_topic_candidate } : a),
        );
      } catch { fetchArticles(); }
    },
    [articles, fetchArticles],
  );

  const handlePageChange = (page: number) => {
    setFilters((prev) => ({ ...prev, page }));
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <div className="space-y-6 pb-12">
      <PageHeader
        title="资讯列表"
        breadcrumbs={[{ label: '首页', href: '/' }, { label: '资讯列表' }]}
      />
      <ArticleFilters filters={filters} onFiltersChange={setFilters} brands={brands} monitorGroups={monitorGroups} />

      {loading ? (
        <div className="flex min-h-[40vh] items-center justify-center">
          <LoadingSpinner size="lg" label="加载资讯中…" />
        </div>
      ) : error ? (
        <ErrorMessage message={error} onRetry={fetchArticles} />
      ) : (
        <>
          <p className="text-2xs text-fg-muted">
            共 <span className="font-medium text-fg-secondary">{total}</span> 条资讯
          </p>
          <ArticleList articles={articles} onToggleBookmark={handleToggleBookmark} onToggleTopicCandidate={handleToggleTopicCandidate} />
          <Pagination page={filters.page || 1} total={total} pageSize={filters.page_size || PAGE_SIZE} onPageChange={handlePageChange} className="mt-6" />
        </>
      )}
    </div>
  );
}
