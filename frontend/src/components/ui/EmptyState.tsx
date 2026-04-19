import clsx from 'clsx';

export default function EmptyState({ title = '暂无数据', description, icon, action, className }: {
  title?: string; description?: string; icon?: React.ReactNode; action?: React.ReactNode; className?: string;
}) {
  return (
    <div className={clsx('flex flex-col items-center justify-center gap-3 py-16 text-center', className)}>
      {icon ?? (
        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-bg-hover border border-border">
          <svg className="h-5 w-5 text-fg-light" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M20.25 7.5l-.625 10.632a2.25 2.25 0 01-2.247 2.118H6.622a2.25 2.25 0 01-2.247-2.118L3.75 7.5m6 4.125l2.25 2.25m0 0l2.25 2.25M12 13.875l2.25-2.25M12 13.875l-2.25 2.25M3.375 7.5h17.25c.621 0 1.125-.504 1.125-1.125v-1.5c0-.621-.504-1.125-1.125-1.125H3.375c-.621 0-1.125.504-1.125 1.125v1.5c0 .621.504 1.125 1.125 1.125z" />
          </svg>
        </div>
      )}
      <div>
        <p className="text-[13px] font-medium text-fg-secondary">{title}</p>
        {description && <p className="mt-1 text-[13px] text-fg-muted">{description}</p>}
      </div>
      {action && <div className="mt-2">{action}</div>}
    </div>
  );
}
