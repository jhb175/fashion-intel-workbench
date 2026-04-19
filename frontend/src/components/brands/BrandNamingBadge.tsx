'use client';

import { useState, useEffect } from 'react';
import { api } from '@/lib/api';
import type { Brand } from '@/types';

export default function BrandNamingBadge({ brandName }: { brandName: string }) {
  const [brand, setBrand] = useState<Brand | null>(null);
  const [expanded, setExpanded] = useState(false);

  useEffect(() => {
    let cancelled = false;
    async function fetchNaming() {
      try {
        const results = await api.get<Brand[]>('/admin/brands/search-naming', { q: brandName });
        const list = Array.isArray(results) ? results : [];
        if (!cancelled && list.length > 0) setBrand(list[0]);
      } catch { /* Non-critical */ }
    }
    if (brandName) fetchNaming();
    return () => { cancelled = true; };
  }, [brandName]);

  if (!brand?.official_name) return null;

  return (
    <span className="relative inline-flex">
      <button onClick={() => setExpanded((v) => !v)}
        className="inline-flex items-center gap-1 rounded-md border border-amber-200 bg-amber-50 px-2 py-0.5 text-2xs font-medium text-amber-700 transition-colors hover:bg-amber-100"
        title="查看品牌官方写法" aria-label={`品牌官方写法：${brand.official_name}`}>
        <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M9.568 3H5.25A2.25 2.25 0 003 5.25v4.318c0 .597.237 1.17.659 1.591l9.581 9.581c.699.699 1.78.872 2.607.33a18.095 18.095 0 005.223-5.223c.542-.827.369-1.908-.33-2.607L11.16 3.66A2.25 2.25 0 009.568 3z" />
          <path strokeLinecap="round" strokeLinejoin="round" d="M6 6h.008v.008H6V6z" />
        </svg>
        {brand.official_name}
      </button>
      {expanded && (
        <div className="absolute left-0 top-full z-20 mt-1 w-60 rounded-lg border border-border bg-white p-3 shadow-panel">
          <p className="text-2xs font-medium text-fg-secondary">品牌官方写法</p>
          <p className="mt-0.5 text-[13px] font-medium text-fg">{brand.official_name}</p>
          {brand.social_media_name && <><p className="mt-2 text-2xs font-medium text-fg-secondary">社交媒体写法</p><p className="mt-0.5 text-[13px] text-fg">{brand.social_media_name}</p></>}
          {brand.naming_notes && <><p className="mt-2 text-2xs font-medium text-fg-secondary">备注</p><p className="mt-0.5 text-2xs text-fg-muted">{brand.naming_notes}</p></>}
        </div>
      )}
    </span>
  );
}
