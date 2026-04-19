'use client';

import Image from 'next/image';
import type { BrandLogo } from '@/types';

const logoTypeLabels: Record<string, string> = { main: '主 Logo', horizontal: '横版', icon: '图标', monochrome: '单色版', other: '其他' };

export default function BrandLogoCard({ logo, onDelete, onDownload }: { logo: BrandLogo; onDelete: () => void; onDownload: () => void }) {
  return (
    <div className="group flex flex-col items-center rounded-lg border border-border bg-bg-hover p-3 transition-colors hover:border-border-hover">
      <div className="flex h-16 w-16 items-center justify-center rounded-md bg-bg-active">
        {logo.thumbnail_path ? (
          <Image src={logo.thumbnail_path} alt={logo.file_name} width={64} height={64} className="h-full w-full object-contain p-1" unoptimized />
        ) : (
          <svg className="h-8 w-8 text-fg-light" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M2.25 15.75l5.159-5.159a2.25 2.25 0 013.182 0l5.159 5.159m-1.5-1.5l1.409-1.409a2.25 2.25 0 013.182 0l2.909 2.909M3.75 21h16.5a2.25 2.25 0 002.25-2.25V5.25a2.25 2.25 0 00-2.25-2.25H3.75a2.25 2.25 0 00-2.25 2.25v13.5A2.25 2.25 0 003.75 21z" /></svg>
        )}
      </div>
      <p className="mt-1.5 w-full truncate text-center text-2xs font-medium text-fg-secondary" title={logo.file_name}>{logo.file_name}</p>
      <div className="mt-0.5 flex items-center gap-1 text-[10px] text-fg-light"><span className="uppercase">{logo.file_format}</span><span>·</span><span>{logoTypeLabels[logo.logo_type] || logo.logo_type}</span></div>
      <div className="mt-2 flex items-center gap-1.5 opacity-0 transition-opacity group-hover:opacity-100">
        <button onClick={onDownload} className="rounded-md border border-border p-1.5 text-fg-muted transition-colors hover:bg-bg-active hover:text-fg" title="下载">
          <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" /></svg>
        </button>
        <button onClick={onDelete} className="rounded-md border border-red-200 p-1.5 text-red-500 transition-colors hover:bg-red-50" title="删除">
          <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" /></svg>
        </button>
      </div>
    </div>
  );
}
