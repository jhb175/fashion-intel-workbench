import clsx from 'clsx';

const sizes = { sm: 'h-4 w-4', md: 'h-6 w-6', lg: 'h-8 w-8' };

export default function LoadingSpinner({ size = 'md', label, className }: {
  size?: 'sm' | 'md' | 'lg'; label?: string; className?: string;
}) {
  return (
    <div className={clsx('flex flex-col items-center justify-center gap-3', className)} role="status">
      <svg className={clsx('animate-spin text-fg-muted', sizes[size])} viewBox="0 0 24 24" fill="none">
        <circle className="opacity-20" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" />
        <path className="opacity-80" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
      </svg>
      {label && <p className="text-[13px] text-fg-muted">{label}</p>}
    </div>
  );
}
