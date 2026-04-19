'use client';
import { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import clsx from 'clsx';

const I = (d: string) => <svg className="h-[18px] w-[18px]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d={d}/></svg>;

const nav = [
  { label:'仪表盘', href:'/', icon:I('M3.75 6A2.25 2.25 0 016 3.75h2.25A2.25 2.25 0 0110.5 6v2.25a2.25 2.25 0 01-2.25 2.25H6a2.25 2.25 0 01-2.25-2.25V6zM3.75 15.75A2.25 2.25 0 016 13.5h2.25a2.25 2.25 0 012.25 2.25V18a2.25 2.25 0 01-2.25 2.25H6A2.25 2.25 0 013.75 18v-2.25zM13.5 6a2.25 2.25 0 012.25-2.25H18A2.25 2.25 0 0120.25 6v2.25A2.25 2.25 0 0118 10.5h-2.25a2.25 2.25 0 01-2.25-2.25V6zM13.5 15.75a2.25 2.25 0 012.25-2.25H18a2.25 2.25 0 012.25 2.25V18A2.25 2.25 0 0118 20.25h-2.25A2.25 2.25 0 0113.5 18v-2.25z') },
  { label:'资讯', href:'/articles', icon:I('M12 7.5h1.5m-1.5 3h1.5m-7.5 3h7.5m-7.5 3h7.5m3-9h3.375c.621 0 1.125.504 1.125 1.125V18a2.25 2.25 0 01-2.25 2.25M16.5 7.5V4.875c0-.621-.504-1.125-1.125-1.125H4.125C3.504 3.75 3 4.254 3 4.875V18a2.25 2.25 0 002.25 2.25h13.5M6 7.5h3v3H6v-3z') },
  { label:'收藏', href:'/bookmarks', icon:I('M17.593 3.322c1.1.128 1.907 1.077 1.907 2.185V21L12 17.25 4.5 21V5.507c0-1.108.806-2.057 1.907-2.185a48.507 48.507 0 0111.186 0z') },
  { label:'简报', href:'/briefings', icon:I('M9 12h3.75M9 15h3.75M9 18h3.75m3 .75H18a2.25 2.25 0 002.25-2.25V6.108c0-1.135-.845-2.098-1.976-2.192a48.424 48.424 0 00-1.123-.08m-5.801 0c-.065.21-.1.433-.1.664 0 .414.336.75.75.75h4.5a.75.75 0 00.75-.75 2.25 2.25 0 00-.1-.664m-5.8 0A2.251 2.251 0 0113.5 2.25H15a2.25 2.25 0 012.15 1.586m-5.8 0c-.376.023-.75.05-1.124.08C9.095 4.01 8.25 4.973 8.25 6.108V8.25m0 0H4.875c-.621 0-1.125.504-1.125 1.125v11.25c0 .621.504 1.125 1.125 1.125h9.75c.621 0 1.125-.504 1.125-1.125V9.375c0-.621-.504-1.125-1.125-1.125H8.25z') },
  { label:'知识库', href:'/knowledge', icon:I('M12 6.042A8.967 8.967 0 006 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 016 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 016-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0018 18a8.967 8.967 0 00-6 2.292m0-14.25v14.25') },
];
const admin = [
  { label:'资讯源', href:'/admin/sources' },
  { label:'品牌池', href:'/admin/brands' },
  { label:'关键词', href:'/admin/keywords' },
  { label:'监控组', href:'/admin/monitor-groups' },
  { label:'AI 配置', href:'/admin/ai-providers' },
];

export default function Sidebar({ open, onClose }: { open: boolean; onClose: () => void }) {
  const p = usePathname();
  const [showAdmin, setShowAdmin] = useState(p.startsWith('/admin'));
  const active = (h: string) => h === '/' ? p === '/' : p.startsWith(h);

  const lnk = (h: string) => clsx(
    'flex items-center gap-2.5 rounded-lg px-3 py-2 text-[13px] transition-colors',
    active(h) ? 'bg-primary-bg text-primary-text font-medium' : 'text-fg-secondary hover:bg-bg-hover hover:text-fg',
  );

  return (
    <>
      {open && <div className="fixed inset-0 z-40 bg-black/20 desktop:hidden" onClick={onClose}/>}
      <aside className={clsx(
        'fixed left-0 top-0 z-50 flex h-full w-[240px] flex-col border-r border-border bg-white transition-transform duration-200',
        'desktop:relative desktop:z-auto desktop:translate-x-0',
        open ? 'translate-x-0' : '-translate-x-full',
      )}>
        {/* Logo */}
        <div className="flex h-14 items-center gap-2.5 border-b border-border px-5">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-gradient-to-br from-primary to-primary-light">
            <span className="text-xs font-bold text-white">潮</span>
          </div>
          <span className="text-[15px] font-semibold text-fg">潮流情报</span>
        </div>

        <nav className="flex-1 overflow-y-auto px-3 py-4">
          <ul className="space-y-0.5">
            {nav.map((n) => (
              <li key={n.href}><Link href={n.href} className={lnk(n.href)}>
                <span className={active(n.href) ? 'text-primary' : 'text-fg-muted'}>{n.icon}</span>{n.label}
              </Link></li>
            ))}
          </ul>

          <div className="my-4 h-px bg-border"/>

          <button onClick={() => setShowAdmin(!showAdmin)} className={clsx(lnk('/admin'), 'w-full')}>
            <span className={active('/admin') ? 'text-primary' : 'text-fg-muted'}>
              {I('M9.594 3.94c.09-.542.56-.94 1.11-.94h2.593c.55 0 1.02.398 1.11.94l.213 1.281c.063.374.313.686.645.87.074.04.147.083.22.127.324.196.72.257 1.075.124l1.217-.456a1.125 1.125 0 011.37.49l1.296 2.247a1.125 1.125 0 01-.26 1.431l-1.003.827c-.293.24-.438.613-.431.992a6.759 6.759 0 010 .255c-.007.378.138.75.43.99l1.005.828c.424.35.534.954.26 1.43l-1.298 2.247a1.125 1.125 0 01-1.369.491l-1.217-.456c-.355-.133-.75-.072-1.076.124a6.57 6.57 0 01-.22.128c-.331.183-.581.495-.644.869l-.213 1.28c-.09.543-.56.941-1.11.941h-2.594c-.55 0-1.02-.398-1.11-.94l-.213-1.281c-.062-.374-.312-.686-.644-.87a6.52 6.52 0 01-.22-.127c-.325-.196-.72-.257-1.076-.124l-1.217.456a1.125 1.125 0 01-1.369-.49l-1.297-2.247a1.125 1.125 0 01.26-1.431l1.004-.827c.292-.24.437-.613.43-.992a6.932 6.932 0 010-.255c.007-.378-.138-.75-.43-.99l-1.004-.828a1.125 1.125 0 01-.26-1.43l1.297-2.247a1.125 1.125 0 011.37-.491l1.216.456c.356.133.751.072 1.076-.124.072-.044.146-.087.22-.128.332-.183.582-.495.644-.869l.214-1.281z')}
            </span>
            <span className="flex-1 text-left">后台管理</span>
            <svg className={clsx('h-3.5 w-3.5 text-fg-muted transition-transform', showAdmin && 'rotate-180')} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5"/></svg>
          </button>
          {showAdmin && (
            <ul className="ml-5 mt-1 space-y-0.5 border-l border-border pl-3">
              {admin.map((a) => (
                <li key={a.href}><Link href={a.href} className={clsx(
                  'block rounded-md px-2.5 py-1.5 text-[13px] transition-colors',
                  active(a.href) ? 'text-primary font-medium' : 'text-fg-muted hover:text-fg-secondary',
                )}>{a.label}</Link></li>
              ))}
            </ul>
          )}
        </nav>

        <div className="border-t border-border px-4 py-3">
          <div className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary-bg text-xs font-medium text-primary">编</div>
            <div className="min-w-0 flex-1">
              <p className="truncate text-[13px] font-medium text-fg">潮流编辑</p>
              <p className="truncate text-2xs text-fg-muted">编辑工作台</p>
            </div>
          </div>
        </div>
      </aside>
    </>
  );
}
