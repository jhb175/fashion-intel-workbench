'use client';

interface Tag { tag_value: string; count: number }

export default function TrendingTags({ data }: { data: Record<string, Tag[]> }) {
  const groups = Object.entries(data);
  if (!groups.length) return null;

  return (
    <section>
      <h2 className="mb-4 text-[15px] font-semibold text-fg">热门标签</h2>
      <div className="grid gap-4 sm:grid-cols-2">
        {groups.map(([name, tags]) => {
          const max = Math.max(...tags.map((t) => t.count), 1);
          return (
            <div key={name} className="rounded-lg border border-border bg-white p-5 shadow-card">
              <h3 className="mb-3 flex items-center gap-2 text-[13px] font-medium text-fg-secondary">
                <span className="h-1.5 w-1.5 rounded-full bg-primary" />{name}
              </h3>
              <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1.5">
                {tags.slice(0, 12).map((t, i) => (
                  <span key={i} className="text-fg-secondary hover:text-primary transition-colors cursor-default"
                    style={{
                      fontSize: t.count / max > 0.6 ? '13px' : '11px',
                      fontWeight: t.count / max > 0.6 ? 600 : 400,
                      opacity: 0.5 + 0.5 * (t.count / max),
                    }}>
                    {t.tag_value}<span className="ml-0.5 text-[10px] text-fg-light">{t.count}</span>
                  </span>
                ))}
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}
