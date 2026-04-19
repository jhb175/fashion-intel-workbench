'use client';

import { useState, useRef, useEffect } from 'react';
import clsx from 'clsx';

export default function DateRangePicker({ startDate, endDate, onChange, className }: {
  startDate: string; endDate: string; onChange: (s: string, e: string) => void; className?: string;
}) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const h = (e: MouseEvent) => { if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false); };
    document.addEventListener('mousedown', h);
    return () => document.removeEventListener('mousedown', h);
  }, []);

  const has = startDate || endDate;
  const display = has ? `${startDate || '…'} 至 ${endDate || '…'}` : '选择日期范围';

  return (
    <div ref={ref} className={clsx('relative', className)}>
      <button onClick={() => setOpen(!open)} className={clsx(
        'flex h-8 items-center gap-2 rounded-lg border px-3 text-[13px] transition-colors',
        has ? 'border-primary/30 bg-primary-bg text-fg-secondary' : 'border-border bg-white text-fg-muted',
        'hover:border-border-hover',
      )}>
        <svg className="h-3.5 w-3.5 text-fg-light" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M6.75 3v2.25M17.25 3v2.25M3 18.75V7.5a2.25 2.25 0 012.25-2.25h13.5A2.25 2.25 0 0121 7.5v11.25m-18 0A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75m-18 0v-7.5A2.25 2.25 0 015.25 9h13.5A2.25 2.25 0 0121 11.25v7.5" />
        </svg>
        <span>{display}</span>
      </button>
      {open && (
        <div className="absolute left-0 top-full z-20 mt-1 rounded-lg border border-border bg-white p-4 shadow-panel">
          <div className="flex items-center gap-3">
            <div>
              <label className="mb-1 block text-2xs text-fg-muted">开始</label>
              <input type="date" value={startDate} onChange={(e) => onChange(e.target.value, endDate)}
                className="h-8 rounded-lg border border-border bg-bg px-2 text-[13px] text-fg focus:border-primary/50 focus:outline-none focus:ring-1 focus:ring-primary/20" />
            </div>
            <span className="mt-5 text-fg-light">—</span>
            <div>
              <label className="mb-1 block text-2xs text-fg-muted">结束</label>
              <input type="date" value={endDate} onChange={(e) => onChange(startDate, e.target.value)}
                className="h-8 rounded-lg border border-border bg-bg px-2 text-[13px] text-fg focus:border-primary/50 focus:outline-none focus:ring-1 focus:ring-primary/20" />
            </div>
          </div>
          {has && (
            <button onClick={() => { onChange('', ''); setOpen(false); }} className="mt-3 text-2xs text-fg-muted hover:text-fg-secondary transition-colors">清除</button>
          )}
        </div>
      )}
    </div>
  );
}
