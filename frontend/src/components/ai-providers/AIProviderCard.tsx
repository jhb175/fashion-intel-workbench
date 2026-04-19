'use client';

import clsx from 'clsx';
import type { AIProvider } from '@/types';
import ConnectionTestButton from '@/components/ai-providers/ConnectionTestButton';

interface AIProviderCardProps {
  provider: AIProvider;
  onEdit: () => void;
  onDelete: () => void;
  onActivate: () => void;
  onTestComplete?: () => void;
}

export default function AIProviderCard({ provider, onEdit, onDelete, onActivate, onTestComplete }: AIProviderCardProps) {
  return (
    <div className={clsx('rounded-lg border bg-white p-4 shadow-card transition-shadow hover:shadow-card-hover', provider.is_active ? 'border-emerald-200' : 'border-border')}>
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-2">
          <h3 className="text-[13px] font-medium text-fg">{provider.name}</h3>
          {provider.is_active && <span className="rounded-md bg-emerald-50 border border-emerald-200 px-1.5 py-0.5 text-2xs font-medium text-emerald-600">当前使用</span>}
          {provider.is_preset && <span className="rounded-md bg-bg-hover border border-border px-1.5 py-0.5 text-2xs font-medium text-fg-muted">预置</span>}
        </div>
      </div>

      <div className="mt-3 space-y-1">
        <div className="flex items-center gap-2 text-2xs"><span className="text-fg-muted w-14">API Key</span><span className="font-mono text-fg-secondary">{provider.api_key_masked}</span></div>
        <div className="flex items-center gap-2 text-2xs"><span className="text-fg-muted w-14">Base URL</span><span className="font-mono text-fg-secondary truncate">{provider.api_base_url}</span></div>
        <div className="flex items-center gap-2 text-2xs"><span className="text-fg-muted w-14">模型</span><span className="font-mono text-fg-secondary">{provider.model_name}</span></div>
      </div>

      {provider.last_test_status && (
        <div className="mt-2 flex items-center gap-2 text-2xs">
          <span className={clsx('inline-flex items-center gap-1 rounded-md border px-1.5 py-0.5 font-medium', provider.last_test_status === 'success' ? 'border-emerald-200 bg-emerald-50 text-emerald-600' : 'border-red-200 bg-red-50 text-red-600')}>
            {provider.last_test_status === 'success' ? '✓ 测试通过' : '✗ 测试失败'}
          </span>
          {provider.last_test_at && <span className="text-fg-light">{new Date(provider.last_test_at).toLocaleString('zh-CN')}</span>}
        </div>
      )}

      <div className="mt-3 flex flex-wrap items-center gap-2">
        {!provider.is_active && <button onClick={onActivate} className="h-7 rounded-lg bg-emerald-50 border border-emerald-200 px-3 text-2xs font-medium text-emerald-600 transition-colors hover:bg-emerald-100">设为当前</button>}
        <button onClick={onEdit} className="h-7 rounded-lg border border-border bg-white px-3 text-2xs font-medium text-fg-secondary transition-colors hover:bg-bg-hover">编辑</button>
        {!provider.is_preset && <button onClick={onDelete} className="h-7 rounded-lg border border-red-200 px-3 text-2xs font-medium text-red-500 transition-colors hover:bg-red-50">删除</button>}
        <div className="ml-auto"><ConnectionTestButton providerId={provider.id} onTestComplete={() => onTestComplete?.()} /></div>
      </div>
    </div>
  );
}
