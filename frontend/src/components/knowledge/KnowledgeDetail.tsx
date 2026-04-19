'use client';

import Image from 'next/image';
import type { KnowledgeEntry, KnowledgeCategory } from '@/types';
import TagBadge from '@/components/ui/TagBadge';

const categoryLabels: Record<KnowledgeCategory, string> = { brand_profile: '品牌档案', style_history: '风格历史', classic_item: '经典单品', person_profile: '人物档案' };
const categoryColors: Record<KnowledgeCategory, string> = { brand_profile: 'bg-amber-50 text-amber-700 border-amber-200', style_history: 'bg-purple-50 text-purple-700 border-purple-200', classic_item: 'bg-emerald-50 text-emerald-700 border-emerald-200', person_profile: 'bg-blue-50 text-blue-700 border-blue-200' };

interface TimelineEvent { year: number; event: string }
interface BrandNamingInfo { official_name?: string; social_media_name?: string; naming_notes?: string }
interface BrandLogoItem { id: string; file_name: string; thumbnail_path: string | null; file_format: string; logo_type: string }

export default function KnowledgeDetail({ entry }: { entry: KnowledgeEntry }) {
  const content = entry.content as Record<string, unknown>;
  const timeline = (content.timeline as TimelineEvent[] | undefined) || [];
  const keyFacts = (content.key_facts as string[] | undefined) || [];
  const description = content.description as string | undefined;
  const foundedYear = content.founded_year as number | undefined;
  const founder = content.founder as string | undefined;
  const headquarters = content.headquarters as string | undefined;
  const relatedStyles = (content.related_styles as string[] | undefined) || [];
  const brandNaming: BrandNamingInfo | undefined = entry.category === 'brand_profile' ? { official_name: content.official_name as string | undefined, social_media_name: content.social_media_name as string | undefined, naming_notes: content.naming_notes as string | undefined } : undefined;
  const brandLogos = (content.logos as BrandLogoItem[] | undefined) || [];

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center gap-3">
        <span className={`inline-flex items-center rounded-md border px-2 py-0.5 text-2xs font-medium ${categoryColors[entry.category]}`}>{categoryLabels[entry.category]}</span>
        <time className="text-2xs text-fg-muted">更新于 {new Date(entry.updated_at).toLocaleDateString('zh-CN', { year: 'numeric', month: 'long', day: 'numeric' })}</time>
      </div>

      {entry.summary && (
        <section className="rounded-lg border border-border bg-white p-5 shadow-card">
          <h2 className="mb-2 text-[14px] font-medium text-fg">概述</h2>
          <p className="text-[13px] leading-relaxed text-fg-secondary">{entry.summary}</p>
        </section>
      )}

      {(foundedYear || founder || headquarters) && (
        <section className="rounded-lg border border-border bg-white p-5 shadow-card">
          <h2 className="mb-3 text-[14px] font-medium text-fg">基本信息</h2>
          <dl className="grid gap-3 sm:grid-cols-3">
            {foundedYear && <div><dt className="text-2xs font-medium text-fg-muted">创立年份</dt><dd className="mt-0.5 text-[13px] text-fg">{foundedYear}</dd></div>}
            {founder && <div><dt className="text-2xs font-medium text-fg-muted">创始人</dt><dd className="mt-0.5 text-[13px] text-fg">{founder}</dd></div>}
            {headquarters && <div><dt className="text-2xs font-medium text-fg-muted">总部</dt><dd className="mt-0.5 text-[13px] text-fg">{headquarters}</dd></div>}
          </dl>
        </section>
      )}

      {brandNaming && (brandNaming.official_name || brandNaming.social_media_name || brandNaming.naming_notes) && (
        <section className="rounded-lg border border-amber-200 bg-amber-50 p-5">
          <h2 className="mb-3 text-[14px] font-medium text-fg">品牌官方写法</h2>
          <dl className="space-y-2">
            {brandNaming.official_name && <div><dt className="text-2xs font-medium text-fg-muted">官方英文写法</dt><dd className="mt-0.5 text-[13px] font-medium text-fg">{brandNaming.official_name}</dd></div>}
            {brandNaming.social_media_name && <div><dt className="text-2xs font-medium text-fg-muted">社交媒体写法</dt><dd className="mt-0.5 text-[13px] text-fg">{brandNaming.social_media_name}</dd></div>}
            {brandNaming.naming_notes && <div><dt className="text-2xs font-medium text-fg-muted">写法备注</dt><dd className="mt-0.5 text-[13px] text-fg-secondary">{brandNaming.naming_notes}</dd></div>}
          </dl>
        </section>
      )}

      {brandLogos.length > 0 && (
        <section className="rounded-lg border border-border bg-white p-5 shadow-card">
          <h2 className="mb-3 text-[14px] font-medium text-fg">品牌 Logo</h2>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
            {brandLogos.map((logo) => (
              <div key={logo.id} className="flex flex-col items-center rounded-lg border border-border bg-bg-hover p-3">
                {logo.thumbnail_path ? (
                  <Image src={logo.thumbnail_path} alt={logo.file_name} width={64} height={64} className="h-16 w-16 object-contain" unoptimized />
                ) : (
                  <div className="flex h-16 w-16 items-center justify-center rounded-md bg-bg-active">
                    <svg className="h-8 w-8 text-fg-light" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M2.25 15.75l5.159-5.159a2.25 2.25 0 013.182 0l5.159 5.159m-1.5-1.5l1.409-1.409a2.25 2.25 0 013.182 0l2.909 2.909M3.75 21h16.5a2.25 2.25 0 002.25-2.25V5.25a2.25 2.25 0 00-2.25-2.25H3.75a2.25 2.25 0 00-2.25 2.25v13.5A2.25 2.25 0 003.75 21z" /></svg>
                  </div>
                )}
                <p className="mt-1.5 text-center text-2xs text-fg-secondary line-clamp-1">{logo.file_name}</p>
                <span className="mt-0.5 text-[10px] uppercase text-fg-light">{logo.file_format} · {logo.logo_type}</span>
              </div>
            ))}
          </div>
        </section>
      )}

      {description && (
        <section className="rounded-lg border border-border bg-white p-5 shadow-card">
          <h2 className="mb-2 text-[14px] font-medium text-fg">详细描述</h2>
          <p className="text-[13px] leading-relaxed text-fg-secondary whitespace-pre-line">{description}</p>
        </section>
      )}

      {timeline.length > 0 && (
        <section className="rounded-lg border border-border bg-white p-5 shadow-card">
          <h2 className="mb-3 text-[14px] font-medium text-fg">时间线</h2>
          <div className="relative space-y-0">
            <div className="absolute left-[23px] top-2 bottom-2 w-px bg-border" />
            {timeline.map((event, i) => (
              <div key={i} className="relative flex items-start gap-4 py-2.5">
                <div className="relative z-10 flex h-[46px] w-[46px] flex-shrink-0 items-center justify-center">
                  <span className="h-2.5 w-2.5 rounded-full border-2 border-fg-muted bg-bg" />
                </div>
                <div className="flex-1 pt-0.5">
                  <span className="text-2xs font-medium text-fg">{event.year}</span>
                  <p className="mt-0.5 text-[13px] text-fg-secondary">{event.event}</p>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {keyFacts.length > 0 && (
        <section className="rounded-lg border border-border bg-white p-5 shadow-card">
          <h2 className="mb-2 text-[14px] font-medium text-fg">关键信息</h2>
          <ul className="space-y-1.5">
            {keyFacts.map((fact, i) => (
              <li key={i} className="flex items-start gap-2 text-[13px] text-fg-secondary">
                <svg className="mt-0.5 h-3.5 w-3.5 flex-shrink-0 text-fg-muted" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                <span>{fact}</span>
              </li>
            ))}
          </ul>
        </section>
      )}

      {relatedStyles.length > 0 && (
        <section className="rounded-lg border border-border bg-white p-5 shadow-card">
          <h2 className="mb-2 text-[14px] font-medium text-fg">相关风格</h2>
          <div className="flex flex-wrap gap-1.5">{relatedStyles.map((style) => <TagBadge key={style} label={style} variant="content_type" />)}</div>
        </section>
      )}

      {(entry.brands.length > 0 || entry.keywords.length > 0) && (
        <section className="rounded-lg border border-border bg-white p-5 shadow-card">
          <h2 className="mb-2 text-[14px] font-medium text-fg">关联标签</h2>
          <div className="flex flex-wrap gap-1.5">
            {entry.brands.map((brand) => <TagBadge key={brand} label={brand} variant="brand" />)}
            {entry.keywords.map((kw) => <TagBadge key={kw} label={kw} variant="keyword" />)}
          </div>
        </section>
      )}
    </div>
  );
}
