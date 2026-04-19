'use client';

import { useState, useEffect, useCallback } from 'react';
import clsx from 'clsx';
import { api } from '@/lib/api';
import type { Source, SourceType, MonitorGroup, PaginatedData } from '@/types';
import PageHeader from '@/components/layout/PageHeader';
import LoadingSpinner from '@/components/ui/LoadingSpinner';
import ErrorMessage from '@/components/ui/ErrorMessage';
import EmptyState from '@/components/ui/EmptyState';
import Pagination from '@/components/ui/Pagination';
import SearchInput from '@/components/ui/SearchInput';
import ConfirmDialog from '@/components/ui/ConfirmDialog';

const PAGE_SIZE = 15;

interface SourceFormData { name: string; url: string; source_type: SourceType; monitor_group_id: string; collect_interval_minutes: number; }
const emptyForm: SourceFormData = { name: '', url: '', source_type: 'rss', monitor_group_id: '', collect_interval_minutes: 60 };
const statusLabels: Record<string, { label: string; color: string }> = {
  success: { label: '正常', color: 'border-emerald-200 bg-emerald-50 text-emerald-600' },
  error: { label: '异常', color: 'border-red-200 bg-red-50 text-red-600' },
};

export default function AdminSourcesPage() {
  const [sources, setSources] = useState<Source[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [monitorGroups, setMonitorGroups] = useState<MonitorGroup[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [form, setForm] = useState<SourceFormData>(emptyForm);
  const [saving, setSaving] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<Source | null>(null);

  useEffect(() => {
    api.get<MonitorGroup[] | { items: MonitorGroup[] }>('/admin/monitor-groups')
      .then((res) => { const list = Array.isArray(res) ? res : (res as { items: MonitorGroup[] }).items || []; setMonitorGroups(list); }).catch(() => {});
  }, []);

  const fetchSources = useCallback(async () => {
    setLoading(true); setError(null);
    try {
      const params: Record<string, string> = { page: String(page), page_size: String(PAGE_SIZE) };
      if (search) params.keyword = search;
      const data = await api.get<PaginatedData<Source>>('/admin/sources', params);
      setSources(data.items); setTotal(data.total);
    } catch { setError('加载资讯源列表失败'); }
    finally { setLoading(false); }
  }, [page, search]);

  useEffect(() => { fetchSources(); }, [fetchSources]);

  const groupName = (groupId: string) => monitorGroups.find((g) => g.id === groupId)?.display_name || groupId;
  const openAdd = () => { setEditingId(null); setForm({ ...emptyForm, monitor_group_id: monitorGroups[0]?.id || '' }); setShowForm(true); };
  const openEdit = (source: Source) => { setEditingId(source.id); setForm({ name: source.name, url: source.url, source_type: source.source_type, monitor_group_id: source.monitor_group_id, collect_interval_minutes: source.collect_interval_minutes }); setShowForm(true); };

  const handleSave = async () => {
    setSaving(true);
    try { if (editingId) { await api.put(`/admin/sources/${editingId}`, form); } else { await api.post('/admin/sources', form); } setShowForm(false); fetchSources(); }
    catch {} finally { setSaving(false); }
  };

  const handleToggle = async (source: Source) => {
    try { await api.patch(`/admin/sources/${source.id}/toggle`); setSources((prev) => prev.map((s) => (s.id === source.id ? { ...s, is_enabled: !s.is_enabled } : s))); }
    catch { fetchSources(); }
  };

  const handleDelete = async () => { if (!deleteTarget) return; try { await api.delete(`/admin/sources/${deleteTarget.id}`); setDeleteTarget(null); fetchSources(); } catch { setDeleteTarget(null); } };

  const [collecting, setCollecting] = useState(false);
  const [collectResult, setCollectResult] = useState<string | null>(null);

  const handleCollectAll = async () => {
    setCollecting(true); setCollectResult(null);
    try {
      const res = await api.post<{ sources_total: number; sources_success: number; sources_failed: number; articles_new: number }>('/admin/collect');
      setCollectResult(`采集完成：${res.sources_success}/${res.sources_total} 个源成功，新增 ${res.articles_new} 条资讯`);
      fetchSources(); // 刷新列表看到最新采集状态
    } catch { setCollectResult('采集失败，请稍后重试'); }
    finally { setCollecting(false); }
  };

  return (
    <div className="space-y-6 pb-12">
      <PageHeader title="资讯源管理" breadcrumbs={[{ label: '首页', href: '/' }, { label: '后台管理' }, { label: '资讯源管理' }]}
        actions={
          <div className="flex items-center gap-2">
            <button onClick={handleCollectAll} disabled={collecting}
              className={clsx('h-8 rounded-lg border px-3 text-[13px] font-medium transition-colors', collecting ? 'border-border bg-bg-hover text-fg-muted cursor-not-allowed' : 'border-primary/30 bg-primary-bg text-primary-text hover:bg-primary/10')}>
              {collecting ? '采集中…' : '⚡ 立即采集全部'}
            </button>
            <button onClick={openAdd} className="h-8 rounded-lg bg-primary px-3 text-[13px] font-medium text-white hover:bg-primary-hover">+ 添加资讯源</button>
          </div>
        } />

      {collectResult && (
        <div className={clsx('rounded-lg border px-4 py-3 text-[13px]', collectResult.includes('失败') ? 'border-red-200 bg-red-50 text-red-600' : 'border-emerald-200 bg-emerald-50 text-emerald-600')}>
          {collectResult}
          <button onClick={() => setCollectResult(null)} className="ml-3 text-2xs underline">关闭</button>
        </div>
      )}

      <SearchInput value={search} onChange={(v) => { setSearch(v); setPage(1); }} placeholder="搜索资讯源…" className="max-w-sm" />

      {showForm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60" onClick={() => setShowForm(false)}>
          <div className="w-full max-w-lg rounded-lg border border-border bg-white p-6 shadow-panel" onClick={(e) => e.stopPropagation()}>
            <h2 className="text-[14px] font-medium text-fg">{editingId ? '编辑资讯源' : '添加资讯源'}</h2>
            <div className="mt-4 space-y-4">
              <div><label className="block text-[13px] font-medium text-fg-secondary">名称</label><input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} className="mt-1 h-8 w-full rounded-lg border border-border bg-bg px-3 text-[13px] text-fg focus:border-primary/50 focus:outline-none focus:ring-1 focus:ring-primary/20" placeholder="资讯源名称" /></div>
              <div><label className="block text-[13px] font-medium text-fg-secondary">URL</label><input value={form.url} onChange={(e) => setForm({ ...form, url: e.target.value })} className="mt-1 h-8 w-full rounded-lg border border-border bg-bg px-3 text-[13px] text-fg focus:border-primary/50 focus:outline-none focus:ring-1 focus:ring-primary/20" placeholder="https://..." /></div>
              <div className="grid grid-cols-2 gap-4">
                <div><label className="block text-[13px] font-medium text-fg-secondary">类型</label><select value={form.source_type} onChange={(e) => setForm({ ...form, source_type: e.target.value as SourceType })} className="mt-1 h-8 w-full rounded-lg border border-border bg-bg px-3 text-[13px] text-fg focus:border-primary/50 focus:outline-none focus:ring-1 focus:ring-primary/20"><option value="rss">RSS</option><option value="web">网页</option></select></div>
                <div><label className="block text-[13px] font-medium text-fg-secondary">监控组</label><select value={form.monitor_group_id} onChange={(e) => setForm({ ...form, monitor_group_id: e.target.value })} className="mt-1 h-8 w-full rounded-lg border border-border bg-bg px-3 text-[13px] text-fg focus:border-primary/50 focus:outline-none focus:ring-1 focus:ring-primary/20">{monitorGroups.map((g) => <option key={g.id} value={g.id}>{g.display_name}</option>)}</select></div>
              </div>
              <div><label className="block text-[13px] font-medium text-fg-secondary">采集间隔（分钟）</label><input type="number" min={5} value={form.collect_interval_minutes} onChange={(e) => setForm({ ...form, collect_interval_minutes: Number(e.target.value) })} className="mt-1 h-8 w-full rounded-lg border border-border bg-bg px-3 text-[13px] text-fg focus:border-primary/50 focus:outline-none focus:ring-1 focus:ring-primary/20" /></div>
            </div>
            <div className="mt-6 flex justify-end gap-2">
              <button onClick={() => setShowForm(false)} className="h-8 rounded-lg border border-border bg-white px-3 text-[13px] font-medium text-fg-secondary hover:bg-bg-hover">取消</button>
              <button onClick={handleSave} disabled={saving || !form.name || !form.url} className="h-8 rounded-lg bg-primary px-3 text-[13px] font-medium text-white hover:bg-primary-hover disabled:opacity-50">{saving ? '保存中…' : '保存'}</button>
            </div>
          </div>
        </div>
      )}

      {loading ? (
        <div className="flex min-h-[40vh] items-center justify-center"><LoadingSpinner size="lg" label="加载资讯源中…" /></div>
      ) : error ? (
        <ErrorMessage message={error} onRetry={fetchSources} />
      ) : sources.length === 0 ? (
        <EmptyState title="暂无资讯源" description="点击上方按钮添加第一个资讯源" action={<button onClick={openAdd} className="h-8 rounded-lg bg-primary px-3 text-[13px] font-medium text-white hover:bg-primary-hover">添加资讯源</button>} />
      ) : (
        <>
          <p className="text-2xs text-fg-muted">共 <span className="font-medium text-fg-secondary">{total}</span> 个资讯源</p>
          <div className="overflow-x-auto rounded-lg border border-border">
            <table className="w-full text-[13px]">
              <thead><tr className="border-b border-border bg-bg-hover">
                <th className="px-4 py-2.5 text-left font-medium text-fg-secondary">名称</th><th className="px-4 py-2.5 text-left font-medium text-fg-secondary">URL</th><th className="px-4 py-2.5 text-left font-medium text-fg-secondary">类型</th><th className="px-4 py-2.5 text-left font-medium text-fg-secondary">监控组</th><th className="px-4 py-2.5 text-center font-medium text-fg-secondary">状态</th><th className="px-4 py-2.5 text-left font-medium text-fg-secondary">最近采集</th><th className="px-4 py-2.5 text-center font-medium text-fg-secondary">采集状态</th><th className="px-4 py-2.5 text-right font-medium text-fg-secondary">操作</th>
              </tr></thead>
              <tbody>
                {sources.map((source) => (
                  <tr key={source.id} className="border-b border-border transition-colors hover:bg-bg-hover">
                    <td className="px-4 py-2.5 font-medium text-fg">{source.name}</td>
                    <td className="max-w-[200px] truncate px-4 py-2.5 text-fg-muted" title={source.url}>{source.url}</td>
                    <td className="px-4 py-2.5"><span className="rounded-md border border-border bg-bg-hover px-1.5 py-0.5 text-2xs font-medium text-fg-secondary uppercase">{source.source_type}</span></td>
                    <td className="px-4 py-2.5 text-fg-secondary">{groupName(source.monitor_group_id)}</td>
                    <td className="px-4 py-2.5 text-center">
                      <button onClick={() => handleToggle(source)} className={clsx('relative inline-flex h-5 w-9 items-center rounded-full transition-colors', source.is_enabled ? 'bg-emerald-500' : 'bg-fg-light')} aria-label={source.is_enabled ? '禁用' : '启用'}>
                        <span className={clsx('inline-block h-3.5 w-3.5 rounded-full bg-white transition-transform', source.is_enabled ? 'translate-x-[18px]' : 'translate-x-[3px]')} />
                      </button>
                    </td>
                    <td className="px-4 py-2.5 text-2xs text-fg-muted">{source.last_collected_at ? new Date(source.last_collected_at).toLocaleString('zh-CN') : '—'}</td>
                    <td className="px-4 py-2.5 text-center">
                      {source.last_collect_status ? <span className={clsx('inline-flex rounded-md border px-1.5 py-0.5 text-2xs font-medium', statusLabels[source.last_collect_status]?.color || 'border-border bg-bg-hover text-fg-muted')}>{statusLabels[source.last_collect_status]?.label || source.last_collect_status}</span> : <span className="text-2xs text-fg-light">—</span>}
                    </td>
                    <td className="px-4 py-2.5 text-right">
                      <div className="flex items-center justify-end gap-1">
                        <button onClick={() => openEdit(source)} className="rounded-md px-2 py-1 text-2xs font-medium text-fg-secondary transition-colors hover:bg-bg-hover">编辑</button>
                        <button onClick={() => setDeleteTarget(source)} className="rounded-md px-2 py-1 text-2xs font-medium text-red-500 transition-colors hover:bg-red-50">删除</button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <Pagination page={page} total={total} pageSize={PAGE_SIZE} onPageChange={(p) => { setPage(p); window.scrollTo({ top: 0, behavior: 'smooth' }); }} className="mt-6" />
        </>
      )}

      <ConfirmDialog open={!!deleteTarget} onOpenChange={(open) => { if (!open) setDeleteTarget(null); }} title="删除资讯源" description={`确定要删除资讯源「${deleteTarget?.name}」吗？此操作不可撤销。`} confirmLabel="删除" variant="danger" onConfirm={handleDelete} />
    </div>
  );
}
