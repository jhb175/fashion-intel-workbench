'use client';
import Link from 'next/link';

export interface Breadcrumb { label: string; href?: string }

export default function PageHeader({ title, description, breadcrumbs, actions }: {
  title: string; description?: string; breadcrumbs?: Breadcrumb[]; actions?: React.ReactNode;
}) {
  return (
    <header className="mb-8">
      {breadcrumbs?.length ? (
        <nav className="mb-2"><ol className="flex items-center gap-1.5 text-[13px] text-fg-muted">
          {breadcrumbs.map((c, i) => (<li key={i} className="flex items-center gap-1.5">
            {i > 0 && <span className="text-fg-light">/</span>}
            {c.href ? <Link href={c.href} className="hover:text-fg-secondary transition-colors">{c.label}</Link> : <span className="text-fg-secondary">{c.label}</span>}
          </li>))}
        </ol></nav>
      ) : null}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-fg">{title}</h1>
          {description && <p className="mt-1 text-[14px] text-fg-secondary">{description}</p>}
        </div>
        {actions && <div className="flex items-center gap-2 pt-1">{actions}</div>}
      </div>
    </header>
  );
}
