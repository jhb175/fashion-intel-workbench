'use client';

import { useState, useEffect, useCallback } from 'react';
import { api } from '@/lib/api';
import type { AIProvider } from '@/types';
import PageHeader from '@/components/layout/PageHeader';
import LoadingSpinner from '@/components/ui/LoadingSpinner';
import ErrorMessage from '@/components/ui/ErrorMessage';
import EmptyState from '@/components/ui/EmptyState';
import ConfirmDialog from '@/components/ui/ConfirmDialog';
import AIProviderList from '@/components/ai-providers/AIProviderList';
import AIProviderForm from '@/components/ai-providers/AIProviderForm';
import type { AIProviderFormData } from '@/components/ai-providers/AIProviderForm';

export default function AdminAIProvidersPage() {
  const [providers, setProviders] = useState<AIProvider[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [editingProvider, setEditingProvider] = useState<AIProvider | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<AIProvider | null>(null);

  const fetchProviders = useCallback(async () => {
    setLoading(true); setError(null);
    try { const res = await api.get<AIProvider[] | { items: AIProvider[] }>('/ai-providers'); setProviders(Array.isArray(res) ? res : (res as { items: AIProvider[] }).items || []); }
    catch { setError('加载 AI 提供者列表失败'); } finally { setLoading(false); }
  }, []);

  useEffect(() => { fetchProviders(); }, [fetchProviders]);

  const openAdd = () => { setEditingProvider(null); setShowForm(true); };
  const openEdit = (provider: AIProvider) => { setEditingProvider(provider); setShowForm(true); };

  const handleSubmit = async (data: AIProviderFormData) => {
    if (editingProvider) {
      const body: Record<string, string> = { name: data.name, api_base_url: data.api_base_url, model_name: data.model_name };
      if (data.api_key) body.api_key = data.api_key;
      await api.put(`/ai-providers/${editingProvider.id}`, body);
    } else { await api.post('/ai-providers', data); }
    setShowForm(false); setEditingProvider(null); fetchProviders();
  };

  const handleActivate = async (provider: AIProvider) => { try { await api.patch(`/ai-providers/${provider.id}/activate`); fetchProviders(); } catch {} };
  const handleDelete = async () => { if (!deleteTarget) return; try { await api.delete(`/ai-providers/${deleteTarget.id}`); setDeleteTarget(null); fetchProviders(); } catch { setDeleteTarget(null); } };

  return (
    <div className="space-y-6 pb-12">
      <PageHeader title="AI 提供者配置" breadcrumbs={[{ label: '首页', href: '/' }, { label: '后台管理' }, { label: 'AI 提供者配置' }]}
        actions={<button onClick={openAdd} className="h-8 rounded-lg bg-primary px-3 text-[13px] font-medium text-white hover:bg-primary-hover">+ 添加提供者</button>} />

      <p className="text-[13px] text-fg-muted">配置 AI 模型提供者。支持 OpenAI 及所有兼容 OpenAI Chat Completions API 协议的第三方模型。</p>

      {showForm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60" onClick={() => { setShowForm(false); setEditingProvider(null); }}>
          <AIProviderForm
            initialData={editingProvider ? { name: editingProvider.name, api_base_url: editingProvider.api_base_url, model_name: editingProvider.model_name, api_key_masked: editingProvider.api_key_masked } : undefined}
            isEditing={!!editingProvider} onSubmit={handleSubmit} onCancel={() => { setShowForm(false); setEditingProvider(null); }} />
        </div>
      )}

      {loading ? (
        <div className="flex min-h-[40vh] items-center justify-center"><LoadingSpinner size="lg" label="加载 AI 提供者中…" /></div>
      ) : error ? (
        <ErrorMessage message={error} onRetry={fetchProviders} />
      ) : providers.length === 0 ? (
        <EmptyState title="暂无 AI 提供者" description="点击上方按钮添加第一个 AI 提供者" action={<button onClick={openAdd} className="h-8 rounded-lg bg-primary px-3 text-[13px] font-medium text-white hover:bg-primary-hover">添加提供者</button>} />
      ) : (
        <AIProviderList providers={providers} onEdit={openEdit} onDelete={setDeleteTarget} onActivate={handleActivate} onRefresh={fetchProviders} />
      )}

      <ConfirmDialog open={!!deleteTarget} onOpenChange={(open) => { if (!open) setDeleteTarget(null); }} title="删除 AI 提供者" description={`确定要删除 AI 提供者「${deleteTarget?.name}」吗？此操作不可撤销。`} confirmLabel="删除" variant="danger" onConfirm={handleDelete} />
    </div>
  );
}
