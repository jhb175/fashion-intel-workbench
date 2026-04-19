import clsx from 'clsx';

type Variant = 'brand' | 'monitor_group' | 'content_type' | 'keyword' | 'default';

const styles: Record<Variant, string> = {
  brand: 'bg-amber-50 text-amber-700 border-amber-200',
  monitor_group: 'bg-blue-50 text-blue-700 border-blue-200',
  content_type: 'bg-purple-50 text-purple-700 border-purple-200',
  keyword: 'bg-emerald-50 text-emerald-700 border-emerald-200',
  default: 'bg-bg-hover text-fg-muted border-border',
};

export default function TagBadge({ label, variant = 'default', onRemove, className }: {
  label: string; variant?: Variant; onRemove?: () => void; className?: string;
}) {
  return (
    <span className={clsx('inline-flex items-center gap-1 rounded-md border px-1.5 py-0.5 text-2xs font-medium', styles[variant], className)}>
      {label}
      {onRemove && (
        <button onClick={onRemove} className="ml-0.5 rounded p-0.5 transition-colors hover:bg-black/5" aria-label={`移除 ${label}`}>
          <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" /></svg>
        </button>
      )}
    </span>
  );
}
