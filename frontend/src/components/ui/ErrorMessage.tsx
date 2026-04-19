'use client';

import clsx from 'clsx';

export default function ErrorMessage({ message, onRetry, className }: {
  message: string; onRetry?: () => void; className?: string;
}) {
  return (
    <div className={clsx('flex flex-col items-center gap-3 rounded-lg border border-red-200 bg-red-50 px-6 py-8 text-center', className)} role="alert">
      <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-red-100">
        <svg className="h-5 w-5 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
        </svg>
      </div>
      <p className="text-[13px] text-red-600">{message}</p>
      {onRetry && (
        <button onClick={onRetry} className="h-7 rounded-lg border border-red-200 bg-red-50 px-3 text-[13px] font-medium text-red-600 transition-colors hover:bg-red-100">
          重试
        </button>
      )}
    </div>
  );
}
