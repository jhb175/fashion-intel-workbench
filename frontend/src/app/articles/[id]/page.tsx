'use client';

import { useState, useEffect, useCallback } from 'react';
import { useParams } from 'next/navigation';
import { api } from '@/lib/api';
import type { Article, ArticleTag, TagType, DeepAnalysis } from '@/types';
import clsx from 'clsx';
import PageHeader from '@/components/layout/PageHeader';
import LoadingSpinner from '@/components/ui/LoadingSpinner';
import ErrorMessage from '@/components/ui/ErrorMessage';
import ArticleDetail from '@/components/articles/ArticleDetail';
import TagEditor from '@/components/articles/TagEditor';
import AIAnalysisPanel from '@/components/articles/AIAnalysisPanel';
import RelatedKnowledge from '@/components/articles/RelatedKnowledge';

export default function ArticleDetailPage() {
  const params = useParams();
  const articleId = params.id as string;

  const [article, setArticle] = useState<Article | null>(null);
  const [analysis, setAnalysis] = useState<DeepAnalysis | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchArticle = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [articleData, analysisData] = await Promise.allSettled([
        api.get<Article>(`/articles/${articleId}`),
        api.get<DeepAnalysis>(`/articles/${articleId}/analysis`),
      ]);
      if (articleData.status === 'fulfilled') {
        setArticle(articleData.value);
      } else {
        throw new Error('加载资讯详情失败');
      }
      if (analysisData.status === 'fulfilled') {
        setAnalysis(analysisData.value);
      }
    } catch {
      setError('加载资讯详情失败，请稍后重试');
    } finally {
      setLoading(false);
    }
  }, [articleId]);

  useEffect(() => { fetchArticle(); }, [fetchArticle]);

  const handleAddTag = useCallback(
    async (tagType: TagType, tagValue: string) => {
      if (!article) return;
      const currentTags = article.tags.map((t) => ({ tag_type: t.tag_type, tag_value: t.tag_value }));
      const updatedTags = [...currentTags, { tag_type: tagType, tag_value: tagValue }];
      await api.patch<ArticleTag[]>(`/articles/${articleId}/tags`, { tags: updatedTags });
      const refreshed = await api.get<Article>(`/articles/${articleId}`);
      setArticle(refreshed);
    },
    [article, articleId],
  );

  const handleRemoveTag = useCallback(
    async (tagType: TagType, tagValue: string) => {
      if (!article) return;
      const updatedTags = article.tags
        .filter((t) => !(t.tag_type === tagType && t.tag_value === tagValue))
        .map((t) => ({ tag_type: t.tag_type, tag_value: t.tag_value }));
      await api.patch<ArticleTag[]>(`/articles/${articleId}/tags`, { tags: updatedTags });
      const refreshed = await api.get<Article>(`/articles/${articleId}`);
      setArticle(refreshed);
    },
    [article, articleId],
  );

  const handleToggleBookmark = useCallback(async () => {
    if (!article) return;
    try {
      if (article.is_bookmarked) {
        await api.delete(`/bookmarks/${articleId}`);
      } else {
        await api.post('/bookmarks', { article_id: articleId });
      }
      setArticle((prev) => prev ? { ...prev, is_bookmarked: !prev.is_bookmarked } : prev);
    } catch { fetchArticle(); }
  }, [article, articleId, fetchArticle]);

  const handleToggleTopicCandidate = useCallback(async () => {
    if (!article) return;
    try {
      if (article.is_topic_candidate) {
        await api.delete(`/topic-candidates/${articleId}`);
      } else {
        await api.post('/topic-candidates', { article_id: articleId });
      }
      setArticle((prev) => prev ? { ...prev, is_topic_candidate: !prev.is_topic_candidate } : prev);
    } catch { fetchArticle(); }
  }, [article, articleId, fetchArticle]);

  if (loading) {
    return <div className="flex min-h-[60vh] items-center justify-center"><LoadingSpinner size="lg" label="加载资讯详情…" /></div>;
  }

  if (error || !article) {
    return (
      <div className="space-y-6 pb-12">
        <PageHeader title="资讯详情" breadcrumbs={[{ label: '首页', href: '/' }, { label: '资讯列表', href: '/articles' }, { label: '详情' }]} />
        <ErrorMessage message={error || '资讯不存在'} onRetry={fetchArticle} />
      </div>
    );
  }

  return (
    <div className="space-y-6 pb-12">
      <PageHeader
        title="资讯详情"
        breadcrumbs={[{ label: '首页', href: '/' }, { label: '资讯列表', href: '/articles' }, { label: '详情' }]}
        actions={
          <div className="flex items-center gap-2">
            <button
              onClick={handleToggleBookmark}
              className={clsx(
                'inline-flex items-center gap-1.5 h-7 rounded-lg border px-3 text-2xs font-medium transition-colors',
                article.is_bookmarked
                  ? 'border-amber-200 bg-amber-50 text-amber-600'
                  : 'border-border bg-white text-fg-secondary hover:bg-bg-hover hover:text-fg',
              )}
              aria-label={article.is_bookmarked ? '取消收藏' : '收藏'}
            >
              <svg className="h-3.5 w-3.5" fill={article.is_bookmarked ? 'currentColor' : 'none'} viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M17.593 3.322c1.1.128 1.907 1.077 1.907 2.185V21L12 17.25 4.5 21V5.507c0-1.108.806-2.057 1.907-2.185a48.507 48.507 0 0111.186 0z" />
              </svg>
              {article.is_bookmarked ? '已收藏' : '收藏'}
            </button>
            <button
              onClick={handleToggleTopicCandidate}
              className={clsx(
                'inline-flex items-center gap-1.5 h-7 rounded-lg border px-3 text-2xs font-medium transition-colors',
                article.is_topic_candidate
                  ? 'border-purple-200 bg-purple-50 text-purple-600'
                  : 'border-border bg-white text-fg-secondary hover:bg-bg-hover hover:text-fg',
              )}
              aria-label={article.is_topic_candidate ? '取消待选题' : '标记待选题'}
            >
              <svg className="h-3.5 w-3.5" fill={article.is_topic_candidate ? 'currentColor' : 'none'} viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.455 2.456L21.75 6l-1.036.259a3.375 3.375 0 00-2.455 2.456z" />
              </svg>
              {article.is_topic_candidate ? '已标记待选题' : '标记待选题'}
            </button>
          </div>
        }
      />

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="space-y-6 lg:col-span-2">
          <section className="rounded-lg border border-border bg-white p-5 shadow-card">
            <ArticleDetail article={article} />
          </section>
          <section className="rounded-lg border border-border bg-white p-5 shadow-card">
            <AIAnalysisPanel articleId={articleId} initialAnalysis={analysis} />
          </section>
        </div>
        <div className="space-y-6">
          <section className="rounded-lg border border-border bg-white p-4 shadow-card">
            <TagEditor tags={article.tags} onAddTag={handleAddTag} onRemoveTag={handleRemoveTag} />
          </section>
          <section className="rounded-lg border border-border bg-white p-4 shadow-card">
            <RelatedKnowledge articleId={articleId} />
          </section>
        </div>
      </div>
    </div>
  );
}
