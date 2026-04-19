'use client';

import { useState } from 'react';
import clsx from 'clsx';
import type { KnowledgeEntry, KnowledgeCategory } from '@/types';
import TagBadge from '@/components/ui/TagBadge';

export interface KnowledgeFormData {
  title: string; category: KnowledgeCategory; content: Record<string, unknown>; summary: string; brands: string[]; keywords: string[];
}

interface KnowledgeEditorProps { initialData?: KnowledgeEntry; onSubmit: (data: KnowledgeFormData) => Promise<void>; onCancel: () => void; }

const CATEGORIES: Array<{ value: KnowledgeCategory; label: string }> = [
  { value: 'brand_profile', label: '品牌档案' }, { value: 'style_history', label: '风格历史' }, { value: 'classic_item', label: '经典单品' }, { value: 'person_profile', label: '人物档案' },
];

export default function KnowledgeEditor({ initialData, onSubmit, onCancel }: KnowledgeEditorProps) {
  const [form, setForm] = useState<KnowledgeFormData>({ title: initialData?.title || '', category: initialData?.category || 'brand_profile', content: initialData?.content || {}, summary: initialData?.summary || '', brands: initialData?.brands || [], keywords: initialData?.keywords || [] });
  const [saving, setSaving] = useState(false);
  const [contentText, setContentText] = useState(JSON.stringify(initialData?.content || {}, null, 2));
  const [contentError, setContentError] = useState<string | null>(null);
  const [brandInput, setBrandInput] = useState('');
  const [keywordInput, setKeywordInput] = useState('');

  const handleContentChange = (text: string) => {
    setContentText(text);
    try { const parsed = JSON.parse(text); setForm((prev) => ({ ...prev, content: parsed })); setContentError(null); }
    catch { setContentError('JSON 格式不正确'); }
  };

  const addBrand = () => { const v = brandInput.trim(); if (v && !form.brands.includes(v)) setForm((prev) => ({ ...prev, brands: [...prev.brands, v] })); setBrandInput(''); };
  const removeBrand = (brand: string) => { setForm((prev) => ({ ...prev, brands: prev.brands.filter((b) => b !== brand) })); };
  const addKeyword = () => { const v = keywordInput.trim(); if (v && !form.keywords.includes(v)) setForm((prev) => ({ ...prev, keywords: [...prev.keywords, v] })); setKeywordInput(''); };
  const removeKeyword = (kw: string) => { setForm((prev) => ({ ...prev, keywords: prev.keywords.filter((k) => k !== kw) })); };

  const handleSubmit = async () => { if (contentError) return; setSaving(true); try { await onSubmit(form); } finally { setSaving(false); } };
  const canSubmit = form.title && !contentError;

  return (
    <div className="w-full max-w-2xl rounded-lg border border-border bg-white p-6 shadow-panel" onClick={(e) => e.stopPropagation()}>
      <h2 className="text-[14px] font-medium text-fg">{initialData ? '编辑知识条目' : '创建知识条目'}</h2>

      <div className="mt-4 space-y-4 max-h-[70vh] overflow-y-auto pr-1">
        <div>
          <label className="block text-[13px] font-medium text-fg-secondary">标题</label>
          <input value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} className="mt-1 h-8 w-full rounded-lg border border-border bg-bg px-3 text-[13px] text-fg focus:border-primary/50 focus:outline-none focus:ring-1 focus:ring-primary/20" placeholder="知识条目标题" />
        </div>

        <div>
          <label className="block text-[13px] font-medium text-fg-secondary">类别</label>
          <div className="mt-1 flex items-center gap-0.5 rounded-lg border border-border bg-white p-0.5 w-fit">
            {CATEGORIES.map((cat) => (
              <button key={cat.value} type="button" onClick={() => setForm({ ...form, category: cat.value })}
                className={clsx('rounded-md px-2.5 py-1 text-2xs font-medium transition-colors', form.category === cat.value ? 'bg-bg-active text-fg' : 'text-fg-muted hover:text-fg-secondary')}>
                {cat.label}
              </button>
            ))}
          </div>
        </div>

        <div>
          <label className="block text-[13px] font-medium text-fg-secondary">摘要</label>
          <textarea value={form.summary} onChange={(e) => setForm({ ...form, summary: e.target.value })} rows={3}
            className="mt-1 w-full rounded-lg border border-border bg-bg px-3 py-2 text-[13px] text-fg focus:border-primary/50 focus:outline-none focus:ring-1 focus:ring-primary/20" placeholder="简要描述…" />
        </div>

        <div>
          <label className="block text-[13px] font-medium text-fg-secondary">结构化内容 <span className="text-2xs text-fg-muted">（JSON 格式）</span></label>
          <textarea value={contentText} onChange={(e) => handleContentChange(e.target.value)} rows={10}
            className={clsx('mt-1 w-full rounded-lg border px-3 py-2 font-mono text-2xs text-fg focus:outline-none focus:ring-1', contentError ? 'border-red-300 focus:border-red-400 focus:ring-red-200' : 'border-border bg-bg focus:border-primary/50 focus:ring-primary/20')} spellCheck={false} />
          {contentError && <p className="mt-1 text-2xs text-red-500">{contentError}</p>}
        </div>

        <div>
          <label className="block text-[13px] font-medium text-fg-secondary">关联品牌</label>
          <div className="mt-1 flex items-center gap-2">
            <input value={brandInput} onChange={(e) => setBrandInput(e.target.value)} onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); addBrand(); } }}
              className="h-8 flex-1 rounded-lg border border-border bg-bg px-3 text-[13px] text-fg focus:border-primary/50 focus:outline-none focus:ring-1 focus:ring-primary/20" placeholder="输入品牌名称后回车" />
            <button type="button" onClick={addBrand} className="h-8 rounded-lg border border-border bg-white px-3 text-[13px] font-medium text-fg-secondary hover:bg-bg-hover">添加</button>
          </div>
          {form.brands.length > 0 && <div className="mt-2 flex flex-wrap gap-1">{form.brands.map((brand) => <TagBadge key={brand} label={brand} variant="brand" onRemove={() => removeBrand(brand)} />)}</div>}
        </div>

        <div>
          <label className="block text-[13px] font-medium text-fg-secondary">关联关键词</label>
          <div className="mt-1 flex items-center gap-2">
            <input value={keywordInput} onChange={(e) => setKeywordInput(e.target.value)} onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); addKeyword(); } }}
              className="h-8 flex-1 rounded-lg border border-border bg-bg px-3 text-[13px] text-fg focus:border-primary/50 focus:outline-none focus:ring-1 focus:ring-primary/20" placeholder="输入关键词后回车" />
            <button type="button" onClick={addKeyword} className="h-8 rounded-lg border border-border bg-white px-3 text-[13px] font-medium text-fg-secondary hover:bg-bg-hover">添加</button>
          </div>
          {form.keywords.length > 0 && <div className="mt-2 flex flex-wrap gap-1">{form.keywords.map((kw) => <TagBadge key={kw} label={kw} variant="keyword" onRemove={() => removeKeyword(kw)} />)}</div>}
        </div>
      </div>

      <div className="mt-6 flex justify-end gap-2">
        <button onClick={onCancel} className="h-8 rounded-lg border border-border bg-white px-3 text-[13px] font-medium text-fg-secondary hover:bg-bg-hover">取消</button>
        <button onClick={handleSubmit} disabled={saving || !canSubmit} className="h-8 rounded-lg bg-primary px-3 text-[13px] font-medium text-white hover:bg-primary-hover disabled:opacity-50">{saving ? '保存中…' : '保存'}</button>
      </div>
    </div>
  );
}
