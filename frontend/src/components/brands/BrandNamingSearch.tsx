'use client';

import { useState, useEffect } from 'react';
import { api } from '@/lib/api';
import type { Brand } from '@/types';
import SearchInput from '@/components/ui/SearchInput';
import BrandNamingCard from '@/components/brands/BrandNamingCard';

export default function BrandNamingSearch({ className }: { className?: string }) {
  const [query, setQuery] = useState('');
  const [debouncedQuery, setDebouncedQuery] = useState('');
  const [results, setResults] = useState<Brand[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => { const timer = setTimeout(() => setDebouncedQuery(query), 300); return () => clearTimeout(timer); }, [query]);

  useEffect(() => {
    if (!debouncedQuery.trim()) { setResults([]); return; }
    let cancelled = false;
    setLoading(true);
    api.get<Brand[]>('/admin/brands/search-naming', { q: debouncedQuery })
      .then((res) => { if (!cancelled) setResults(Array.isArray(res) ? res : []); })
      .catch(() => { if (!cancelled) setResults([]); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [debouncedQuery]);

  return (
    <div className={className}>
      <SearchInput value={query} onChange={setQuery} placeholder="搜索品牌写法…" className="max-w-md" />
      {loading && <p className="mt-2 text-2xs text-fg-muted">搜索中…</p>}
      {!loading && debouncedQuery && results.length === 0 && <p className="mt-2 text-2xs text-fg-muted">未找到匹配的品牌</p>}
      {!loading && results.length > 0 && (
        <div className="mt-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {results.map((brand) => <BrandNamingCard key={brand.id} brand={brand} />)}
        </div>
      )}
    </div>
  );
}
