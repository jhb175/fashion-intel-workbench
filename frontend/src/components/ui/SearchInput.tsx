'use client';

import { useRef } from 'react';
import clsx from 'clsx';

export default function SearchInput({ value, onChange, placeholder = '搜索…', className }: {
  value: string; onChange: (v: string) => void; placeholder?: string; className?: string;
}) {
  const ref = useRef<HTMLInputElement>(null);
  return (
    <div className={clsx('relative', className)}>
      <svg className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-fg-light" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" />
      </svg>
      <input ref={ref} type="search" value={value} onChange={(e) => onChange(e.target.value)} placeholder={placeholder}
        className="h-8 w-full rounded-lg border border-border bg-white pl-9 pr-8 text-[13px] text-fg placeholder:text-fg-light transition-colors focus:border-primary/50 focus:outline-none focus:ring-1 focus:ring-primary/20" />
      {value && (
        <button onClick={() => { onChange(''); ref.current?.focus(); }}
          className="absolute right-2.5 top-1/2 -translate-y-1/2 rounded p-0.5 text-fg-light transition-colors hover:text-fg-secondary" aria-label="清除">
          <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" /></svg>
        </button>
      )}
    </div>
  );
}
