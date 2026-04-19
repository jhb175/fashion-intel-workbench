'use client';

import { useState, useEffect, useCallback } from 'react';
import clsx from 'clsx';
import type { ArticleFilters as ArticleFiltersType } from '@/types';
import SearchInput from '@/components/ui/SearchInput';
import DateRangePicker from '@/components/ui/DateRangePicker';

interface ArticleFiltersProps {
  filters: ArticleFiltersType;
  onFiltersChange: (filters: ArticleFiltersType) => void;
  brands: string[];
  monitorGroups: Array<{ name: string; display_name: string }>;
  className?: string;
}

const CONTENT_TYPES = [
  '联名', '新品', '秀场', '广告', 'lookbook',
  '品牌动态', '快闪展览', '穿搭', '球鞋配饰', '行业趋势',
];

export default function ArticleFilters({
  filters,
  onFiltersChange,
  brands,
  monitorGroups,
  className,
}: ArticleFiltersProps) {
  const [keyword, setKeyword] = useState(filters.keyword || '');

  useEffect(() => {
    const timer = setTimeout(() => {
      if (keyword !== (filters.keyword || '')) {
        onFiltersChange({ ...filters, keyword: keyword || undefined, page: 1 });
      }
    }, 400);
    return () => clearTimeout(timer);
  }, [keyword]); // eslint-disable-line react-hooks/exhaustive-deps

  const updateFilter = useCallback(
    (key: keyof ArticleFiltersType, value: string | undefined) => {
      onFiltersChange({ ...filters, [key]: value, page: 1 });
    },
    [filters, onFiltersChange],
  );

  const handleDateChange = useCallback(
    (start: string, end: string) => {
      onFiltersChange({
        ...filters,
        start_date: start || undefined,
        end_date: end || undefined,
        page: 1,
      });
    },
    [filters, onFiltersChange],
  );

  const activeCount = [
    filters.brand,
    filters.monitor_group,
    filters.content_type,
    filters.start_date || filters.end_date,
    filters.keyword,
  ].filter(Boolean).length;

  const clearAll = () => {
    setKeyword('');
    onFiltersChange({ page: 1, page_size: filters.page_size });
  };

  return (
    <div className={clsx('space-y-3', className)}>
      <SearchInput
        value={keyword}
        onChange={setKeyword}
        placeholder="搜索资讯（中文摘要、英文标题、标签）…"
        className="max-w-md"
      />

      <div className="flex flex-wrap items-center gap-2">
        {/* Monitor group tabs */}
        <div className="flex items-center gap-0.5 rounded-lg border border-border bg-white p-0.5">
          <button
            onClick={() => updateFilter('monitor_group', undefined)}
            className={clsx(
              'rounded-md px-2.5 py-1 text-2xs font-medium transition-colors',
              !filters.monitor_group ? 'bg-bg-active text-fg' : 'text-fg-muted hover:text-fg-secondary',
            )}
          >
            全部
          </button>
          {monitorGroups.map((group) => (
            <button
              key={group.name}
              onClick={() =>
                updateFilter('monitor_group', filters.monitor_group === group.name ? undefined : group.name)
              }
              className={clsx(
                'rounded-md px-2.5 py-1 text-2xs font-medium transition-colors',
                filters.monitor_group === group.name ? 'bg-bg-active text-fg' : 'text-fg-muted hover:text-fg-secondary',
              )}
            >
              {group.display_name}
            </button>
          ))}
        </div>

        {/* Brand dropdown */}
        <select
          value={filters.brand || ''}
          onChange={(e) => updateFilter('brand', e.target.value || undefined)}
          className="h-8 rounded-lg border border-border bg-white px-3 text-[13px] text-fg-secondary transition-colors hover:border-border-hover focus:border-primary/50 focus:outline-none focus:ring-1 focus:ring-primary/20"
        >
          <option value="">全部品牌</option>
          {brands.map((brand) => (
            <option key={brand} value={brand}>{brand}</option>
          ))}
        </select>

        {/* Content type dropdown */}
        <select
          value={filters.content_type || ''}
          onChange={(e) => updateFilter('content_type', e.target.value || undefined)}
          className="h-8 rounded-lg border border-border bg-white px-3 text-[13px] text-fg-secondary transition-colors hover:border-border-hover focus:border-primary/50 focus:outline-none focus:ring-1 focus:ring-primary/20"
        >
          <option value="">全部类型</option>
          {CONTENT_TYPES.map((type) => (
            <option key={type} value={type}>{type}</option>
          ))}
        </select>

        <DateRangePicker
          startDate={filters.start_date || ''}
          endDate={filters.end_date || ''}
          onChange={handleDateChange}
        />

        {activeCount > 0 && (
          <div className="flex items-center gap-2">
            <span className="inline-flex items-center gap-1 rounded-md bg-primary-bg px-2 py-1 text-2xs font-medium text-primary">
              {activeCount} 个筛选
            </span>
            <button onClick={clearAll} className="text-2xs text-fg-muted transition-colors hover:text-fg">
              清除全部
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
