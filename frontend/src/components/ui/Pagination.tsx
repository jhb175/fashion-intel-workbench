'use client';

import clsx from 'clsx';

export default function Pagination({ page, total, pageSize, onPageChange, className }: {
  page: number; total: number; pageSize: number; onPageChange: (p: number) => void; className?: string;
}) {
  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  if (totalPages <= 1) return null;

  function pages(): (number | 'e')[] {
    const r: (number | 'e')[] = [];
    for (let i = 1; i <= totalPages; i++) {
      if (i === 1 || i === totalPages || (i >= page - 1 && i <= page + 1)) r.push(i);
      else if (r[r.length - 1] !== 'e') r.push('e');
    }
    return r;
  }

  const btn = 'rounded-md p-1.5 text-fg-muted transition-colors hover:bg-bg-hover hover:text-fg-secondary disabled:opacity-30 disabled:cursor-not-allowed';

  return (
    <nav aria-label="分页" className={clsx('flex items-center justify-center gap-1', className)}>
      <button onClick={() => onPageChange(page - 1)} disabled={page <= 1} className={btn} aria-label="上一页">
        <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M15.75 19.5L8.25 12l7.5-7.5" /></svg>
      </button>
      {pages().map((item, i) =>
        item === 'e' ? <span key={`e${i}`} className="px-1 text-[13px] text-fg-light">…</span> : (
          <button key={item} onClick={() => onPageChange(item)} className={clsx(
            'min-w-[28px] rounded-md px-2 py-1 text-[13px] font-medium transition-colors',
            item === page ? 'bg-primary-bg text-primary' : 'text-fg-muted hover:bg-bg-hover hover:text-fg-secondary',
          )} aria-current={item === page ? 'page' : undefined}>{item}</button>
        ),
      )}
      <button onClick={() => onPageChange(page + 1)} disabled={page >= totalPages} className={btn} aria-label="下一页">
        <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" /></svg>
      </button>
    </nav>
  );
}
