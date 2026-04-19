'use client';

import { useState, useEffect, useCallback } from 'react';
import { api } from '@/lib/api';
import type { MonitorGroup } from '@/types';
import PageHeader from '@/components/layout/PageHeader';
import LoadingSpinner from '@/components/ui/LoadingSpinner';
import ErrorMessage from '@/components/ui/ErrorMessage';
import EmptyState from '@/components/ui/EmptyState';

export default function AdminMonitorGroupsPage() {
  const [groups, setGroups] = useState<MonitorGroup[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editForm, setEditForm] = useState({ display_name: '', description: '' });
  const [saving, setSaving] = useState(false);

  const fetchGroups = useCallback(async () => {
    setLoading(true); setError(null);
    try { const res = await api.get<MonitorGroup[] | { items: MonitorGroup[] }>('/admin/monitor-groups'); setGroups(Array.isArray(res) ? res : (res as { items: MonitorGroup[] }).items || []); }
    catch { setError('加载监控组列表失败'); } finally { setLoading(false); }
  }, []);

  useEffect(() => { fetchGroups(); }, [fetchGroups]);

  const openEdit = (group: MonitorGroup) => { setEditingId(group.id); setEditForm({ display_name: group.display_name, description: group.description || '' }); };
  const handleSave = async () => { if (!editingId) return; setSaving(true); try { await api.put(`/admin/monitor-groups/${editingId}`, editForm); setEditingId(null); fetchGroups(); } catch {} finally { setSaving(false); } };

  return (
    <div className="space-y-6 pb-12">
      <PageHeader title="监控组管理" breadcrumbs={[{ label: '首页', href: '/' }, { label: '后台管理' }, { label: '监控组管理' }]} />
      <p className="text-[13px] text-fg-muted">监控组用于对资讯源、品牌和关键词进行分组管理。第一版预置四个监控组，可编辑显示名称和描述。</p>

      {loading ? (
        <div className="flex min-h-[40vh] items-center justify-center"><LoadingSpinner size="lg" label="加载监控组中…" /></div>
      ) : error ? (
        <ErrorMessage message={error} onRetry={fetchGroups} />
      ) : groups.length === 0 ? (
        <EmptyState title="暂无监控组" />
      ) : (
        <div className="grid gap-3 sm:grid-cols-2">
          {groups.map((group) => (
            <div key={group.id} className="rounded-lg border border-border bg-white p-4 shadow-card transition-shadow hover:shadow-card-hover">
              {editingId === group.id ? (
                <div className="space-y-3">
                  <div><label className="block text-2xs font-medium text-fg-muted">标识名称</label><p className="mt-0.5 text-[13px] font-medium text-fg-muted">{group.name}</p></div>
                  <div><label className="block text-2xs font-medium text-fg-muted">显示名称</label><input value={editForm.display_name} onChange={(e) => setEditForm({ ...editForm, display_name: e.target.value })} className="mt-1 h-8 w-full rounded-lg border border-border bg-bg px-3 text-[13px] text-fg focus:border-primary/50 focus:outline-none focus:ring-1 focus:ring-primary/20" /></div>
                  <div><label className="block text-2xs font-medium text-fg-muted">描述</label><textarea value={editForm.description} onChange={(e) => setEditForm({ ...editForm, description: e.target.value })} rows={2} className="mt-1 w-full rounded-lg border border-border bg-bg px-3 py-2 text-[13px] text-fg focus:border-primary/50 focus:outline-none focus:ring-1 focus:ring-primary/20" /></div>
                  <div className="flex justify-end gap-2">
                    <button onClick={() => setEditingId(null)} className="h-7 rounded-lg border border-border bg-white px-3 text-2xs font-medium text-fg-secondary hover:bg-bg-hover">取消</button>
                    <button onClick={handleSave} disabled={saving || !editForm.display_name} className="h-7 rounded-lg bg-primary px-3 text-2xs font-medium text-white hover:bg-primary-hover disabled:opacity-50">{saving ? '保存中…' : '保存'}</button>
                  </div>
                </div>
              ) : (
                <div>
                  <div className="flex items-start justify-between">
                    <div><h3 className="text-[14px] font-medium text-fg">{group.display_name}</h3><p className="mt-0.5 text-2xs text-fg-muted">{group.name}</p></div>
                    <button onClick={() => openEdit(group)} className="rounded-md px-2 py-1 text-2xs font-medium text-fg-secondary transition-colors hover:bg-bg-hover">编辑</button>
                  </div>
                  {group.description && <p className="mt-2 text-[13px] text-fg-secondary">{group.description}</p>}
                  <div className="mt-2 flex items-center gap-3 text-2xs text-fg-muted">
                    <span>排序: {group.sort_order}</span>
                    <span>创建于 {new Date(group.created_at).toLocaleDateString('zh-CN')}</span>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
