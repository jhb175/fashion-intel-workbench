'use client';

import type { Brand } from '@/types';

export default function BrandNamingCard({ brand }: { brand: Brand }) {
  return (
    <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 transition-colors hover:border-amber-300">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-[13px] font-medium text-fg">{brand.name_zh}</p>
          <p className="mt-0.5 text-2xs text-fg-muted">{brand.name_en}</p>
        </div>
        <svg className="h-3.5 w-3.5 text-amber-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M9.568 3H5.25A2.25 2.25 0 003 5.25v4.318c0 .597.237 1.17.659 1.591l9.581 9.581c.699.699 1.78.872 2.607.33a18.095 18.095 0 005.223-5.223c.542-.827.369-1.908-.33-2.607L11.16 3.66A2.25 2.25 0 009.568 3z" />
          <path strokeLinecap="round" strokeLinejoin="round" d="M6 6h.008v.008H6V6z" />
        </svg>
      </div>
      {brand.official_name && <div className="mt-2"><p className="text-[10px] font-medium uppercase tracking-wider text-fg-light">官方写法</p><p className="mt-0.5 text-[13px] font-medium text-fg">{brand.official_name}</p></div>}
      {brand.social_media_name && <div className="mt-1.5"><p className="text-[10px] font-medium uppercase tracking-wider text-fg-light">社交媒体</p><p className="mt-0.5 text-[13px] text-fg-secondary">{brand.social_media_name}</p></div>}
      {brand.naming_notes && <p className="mt-1.5 text-2xs text-fg-muted italic">{brand.naming_notes}</p>}
    </div>
  );
}
