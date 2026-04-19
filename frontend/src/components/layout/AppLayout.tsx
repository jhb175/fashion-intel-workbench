'use client';
import { useState } from 'react';
import { usePathname } from 'next/navigation';
import Sidebar from './Sidebar';

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const p = usePathname();
  const [open, setOpen] = useState(false);
  if (p.startsWith('/login')) return <>{children}</>;

  return (
    <div className="flex h-screen overflow-hidden bg-bg">
      <Sidebar open={open} onClose={() => setOpen(false)} />
      <div className="flex flex-1 flex-col overflow-hidden">
        <header className="flex h-14 items-center border-b border-border bg-white px-5 desktop:hidden">
          <button onClick={() => setOpen(true)} className="mr-3 rounded-lg p-1.5 text-fg-secondary hover:bg-bg-hover hover:text-fg">
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5"/></svg>
          </button>
          <span className="text-sm font-semibold text-fg">潮流情报</span>
        </header>
        <main className="flex-1 overflow-y-auto">
          <div className="mx-auto max-w-[1120px] px-6 py-8 lg:px-10">{children}</div>
        </main>
      </div>
    </div>
  );
}
