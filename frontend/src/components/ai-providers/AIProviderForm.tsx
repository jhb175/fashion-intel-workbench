'use client';

import { useState } from 'react';
import APIKeyInput from '@/components/ai-providers/APIKeyInput';

export interface AIProviderFormData { name: string; api_key: string; api_base_url: string; model_name: string; }

interface AIProviderFormProps { initialData?: Partial<AIProviderFormData> & { api_key_masked?: string }; onSubmit: (data: AIProviderFormData) => Promise<void>; onCancel: () => void; isEditing?: boolean; }

export default function AIProviderForm({ initialData, onSubmit, onCancel, isEditing = false }: AIProviderFormProps) {
  const [form, setForm] = useState<AIProviderFormData>({ name: initialData?.name || '', api_key: '', api_base_url: initialData?.api_base_url || '', model_name: initialData?.model_name || '' });
  const [saving, setSaving] = useState(false);

  const handleSubmit = async () => { setSaving(true); try { await onSubmit(form); } finally { setSaving(false); } };
  const canSubmit = form.name && form.api_base_url && form.model_name && (isEditing || form.api_key);

  return (
    <div className="w-full max-w-lg rounded-lg border border-border bg-white p-6 shadow-panel" onClick={(e) => e.stopPropagation()}>
      <h2 className="text-[14px] font-medium text-fg">{isEditing ? '编辑 AI 提供者' : '添加 AI 提供者'}</h2>
      <div className="mt-4 space-y-4">
        <div>
          <label className="block text-[13px] font-medium text-fg-secondary">提供者名称</label>
          <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} className="mt-1 h-8 w-full rounded-lg border border-border bg-bg px-3 text-[13px] text-fg focus:border-primary/50 focus:outline-none focus:ring-1 focus:ring-primary/20" placeholder="如 OpenAI、DeepSeek" />
        </div>
        <div>
          <label className="block text-[13px] font-medium text-fg-secondary">API Key{isEditing && <span className="ml-1 text-2xs text-fg-muted">（留空则不修改）</span>}</label>
          <APIKeyInput value={form.api_key} onChange={(v) => setForm({ ...form, api_key: v })} maskedValue={initialData?.api_key_masked} className="mt-1" />
        </div>
        <div>
          <label className="block text-[13px] font-medium text-fg-secondary">API Base URL</label>
          <input value={form.api_base_url} onChange={(e) => setForm({ ...form, api_base_url: e.target.value })} className="mt-1 h-8 w-full rounded-lg border border-border bg-bg px-3 text-[13px] font-mono text-fg focus:border-primary/50 focus:outline-none focus:ring-1 focus:ring-primary/20" placeholder="https://api.openai.com/v1" />
        </div>
        <div>
          <label className="block text-[13px] font-medium text-fg-secondary">模型名称</label>
          <input value={form.model_name} onChange={(e) => setForm({ ...form, model_name: e.target.value })} className="mt-1 h-8 w-full rounded-lg border border-border bg-bg px-3 text-[13px] font-mono text-fg focus:border-primary/50 focus:outline-none focus:ring-1 focus:ring-primary/20" placeholder="gpt-4o" />
        </div>
      </div>
      <div className="mt-6 flex justify-end gap-2">
        <button onClick={onCancel} className="h-8 rounded-lg border border-border bg-white px-3 text-[13px] font-medium text-fg-secondary hover:bg-bg-hover">取消</button>
        <button onClick={handleSubmit} disabled={saving || !canSubmit} className="h-8 rounded-lg bg-primary px-3 text-[13px] font-medium text-white hover:bg-primary-hover disabled:opacity-50">{saving ? '保存中…' : '保存'}</button>
      </div>
    </div>
  );
}
