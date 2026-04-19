'use client';

import type { Article } from '@/types';
import ArticleCard from './ArticleCard';
import EmptyState from '@/components/ui/EmptyState';

interface ArticleListProps {
  articles: Article[];
  onToggleBookmark: (articleId: string) => void;
  onToggleTopicCandidate: (articleId: string) => void;
}

export default function ArticleList({
  articles,
  onToggleBookmark,
  onToggleTopicCandidate,
}: ArticleListProps) {
  if (articles.length === 0) {
    return (
      <EmptyState
        title="暂无资讯"
        description="当前筛选条件下没有找到资讯，请尝试调整筛选条件"
      />
    );
  }

  return (
    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
      {articles.map((article) => (
        <ArticleCard
          key={article.id}
          article={article}
          onToggleBookmark={onToggleBookmark}
          onToggleTopicCandidate={onToggleTopicCandidate}
        />
      ))}
    </div>
  );
}
