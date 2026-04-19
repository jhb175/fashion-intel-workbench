'use client';

import { useState, useEffect, useCallback } from 'react';
import { api } from '@/lib/api';
import type { Keyword, MonitorGroup, PaginatedData } from '@/types';
import PageHeader from '@/components/layout/PageHeader';
import LoadingSpinner from '@/components/ui/LoadingSpinner';
import ErrorMessage from '@/components/ui/ErrorMessage';
import EmptyState from '@/components/ui/EmptyState';
import Pagination from '@/components/ui/Pagination';
import SearchInput from '@/components/ui/SearchInput';
import ConfirmDialog from '@/components/ui/ConfirmDialog';

const PAGE_SIZE = 20;
interface KeywordFormData { word_zh: string; word_en: string; monitor_group_id: string; }
const emptyForm: KeywordFormData = { word_zh: '', word_en: '', monitor_group_id: '' };

export default function AdminKeywordsPage() {
  const [keywords, setKeywords] = useState<Keyword[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [monitorGroups, setMonitorGroups] = useState<MonitorGroup[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [form, setForm] = useState<KeywordFormData>(emptyForm);
  const [saving, setSaving] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<Keyword | null>(null);

  useEffect(() => { api.get<MonitorGroup[] | { items: MonitorGroup[] }>('/admin/monitor-groups').then((res) => { setMonitorGroups(Array.isArray(res) ? res : (res as { items: MonitorGroup[] }).items || []); }).catch(() => {}); }, []);

  const fetchKeywords = useCallback(async () => {
    setLoading(true); setError(null);
    try { const params: Record<string, string> = { page: String(page), page_size: String(PAGE_SIZE) }; if (search) params.keyword = search; const data = await api.get<PaginatedData<Keyword>>('/admin/keywords', params); setKeywords(data.items); setTotal(data.total); }
    catch { setError('加载关键词列表失败'); } finally { setLoading(false); }
  }, [page, search]);

  useEffect(() => { fetchKeywords(); }, [fetchKeywords]);

  const groupName = (groupId: string) => monitorGroups.find((g) => g.id === groupId)?.display_name || groupId;
  const openAdd = () => { setEditingId(null); setForm({ ...emptyForm, monitor_group_id: monitorGroups[0]?.id || '' }); setShowForm(true); };
  const openEdit = (kw: Keyword) => { setEditingId(kw.id); setForm({ word_zh: kw.word_zh, word_en: kw.word_en, monitor_group_id: kw.monitor_group_id }); setShowForm(true); };
  const handleSave = async () => { setSaving(true); try { if (editingId) { await api.put(`/admin/keywords/${editingId}`, form); } else { await api.post('/admin/keywords', form); } setShowForm(false); fetchKeywords(); } catch {} finally { setSaving(false); } };
  const handleDelete = async () => { if (!deleteTarget) return; try { await api.delete(`/admin/keywords/${deleteTarget.id}`); setDeleteTarget(null); fetchKeywords(); } catch { setDeleteTarget(null); } };

  return (
    <div className="space-y-6 pb-12">
      <PageHeader title="关键词池管理" breadcrumbs={[{ label: '首页', href: '/' }, { label: '后台管理' }, { label: '关键词池管理' }]}
        actions={<button onClick={openAdd} className="h-8 rounded-lg bg-primary px-3 text-[13px] font-medium text-white hover:bg-primary-hover">+ 添加关键词</button>} />

      <SearchInput value={search} onChange={(v) => { setSearch(v); setPage(1); }} placeholder="搜索关键词…" className="max-w-sm" />

      {showForm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60" onClick={() => setShowForm(false)}>
          <div className="w-full max-w-md rounded-lg border border-border bg-white p-6 shadow-panel" onClick={(e) => e.stopPropagation()}>
            <h2 className="text-[14px] font-medium text-fg">{editingId ? '编辑关键词' : '添加关键词'}</h2>
            <div className="mt-4 space-y-4">
              <div><label className="block text-[13px] font-medium text-fg-secondary">中文词</label><input value={form.word_zh} onChange={(e) => setForm({ ...form, word_zh: e.target.value })} className="mt-1 h-8 w-full rounded-lg border border-border bg-bg px-3 text-[13px] text-fg focus:border-primary/50 focus:outline-none focus:ring-1 focus:ring-primary/20" placeholder="中文关键词" /></div>
              <div><label className="block text-[13px] font-medium text-fg-secondary">英文词</label><input value={form.word_en} onChange={(e) => setForm({ ...form, word_en: e.target.value })} className="mt-1 h-8 w-full rounded-lg border border-border bg-bg px-3 text-[13px] text-fg focus:border-primary/50 focus:outline-none focus:ring-1 focus:ring-primary/20" placeholder="English keyword" /></div>
              <div><label className="block text-[13px] font-medium text-fg-secondary">监控组</label><select value={form.monitor_group_id} onChange={(e) => setForm({ ...form, monitor_group_id: e.target.value })} className="mt-1 h-8 w-full rounded-lg border border-border bg-bg px-3 text-[13px] text-fg focus:border-primary/50 focus:outline-none focus:ring-1 focus:ring-primary/20">{monitorGroups.map((g) => <option key={g.id} value={g.id}>{g.display_name}</option>)}</select></div>
            </div>
            <div className="mt-6 flex justify-end gap-2">
              <button onClick={() => setShowForm(false)} className="h-8 rounded-lg border border-border bg-white px-3 text-[13px] font-medium text-fg-secondary hover:bg-bg-hover">取消</button>
              <button onClick={handleSave} disabled={saving || !form.word_zh || !form.word_en} className="h-8 rounded-lg bg-primary px-3 text-[13px] font-medium text-white hover:bg-primary-hover disabled:opacity-50">{saving ? '保存中…' : '保存'}</button>
            </div>
          </div>
        </div>
      )}

      {loading ? (
        <div className="flex min-h-[40vh] items-center justify-center"><LoadingSpinner size="lg" label="加载关键词中…" /></div>
      ) : error ? (
        <ErrorMessage message={error} onRetry={fetchKeywords} />
      ) : keywords.length === 0 ? (
        <EmptyState title="暂无关键词" description="点击上方按钮添加第一个关键词" action={<button onClick={openAdd} className="h-8 rounded-lg bg-primary px-3 text-[13px] font-medium text-white hover:bg-primary-hover">添加关键词</button>} />
      ) : (
        <>
          <p className="text-2xs text-fg-muted">共 <span className="font-medium text-fg-secondary">{total}</span> 个关键词</p>
          <div className="overflow-x-auto rounded-lg border border-border">
            <table className="w-full text-[13px]">
              <thead><tr className="border-b border-border bg-bg-hover">
                <th className="px-4 py-2.5 text-left font-medium text-fg-secondary">中文词</th><th className="px-4 py-2.5 text-left font-medium text-fg-secondary">英文词</th><th className="px-4 py-2.5 text-left font-medium text-fg-secondary">监控组</th><th className="px-4 py-2.5 text-left font-medium text-fg-secondary">创建时间</th><th className="px-4 py-2.5 text-right font-medium text-fg-secondary">操作</th>
              </tr></thead>
              <tbody>
                {keywords.map((kw) => (
                  <tr key={kw.id} className="border-b border-border transition-colors hover:bg-bg-hover">
                    <td className="px-4 py-2.5 font-medium text-fg">{kw.word_zh}</td>
                    <td className="px-4 py-2.5 text-fg-secondary">{kw.word_en}</td>
                    <td className="px-4 py-2.5 text-fg-muted">{groupName(kw.monitor_group_id)}</td>
                    <td className="px-4 py-2.5 text-2xs text-fg-muted">{new Date(kw.created_at).toLocaleDateString('zh-CN')}</td>
                    <td className="px-4 py-2.5 text-right">
                      <div className="flex items-center justify-end gap-1">
                        <button onClick={() => openEdit(kw)} className="rounded-md px-2 py-1 text-2xs font-medium text-fg-secondary transition-colors hover:bg-bg-hover">编辑</button>
                        <button onClick={() => setDeleteTarget(kw)} className="rounded-md px-2 py-1 text-2xs font-medium text-red-500 transition-colors hover:bg-red-50">删除</button>
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

      <ConfirmDialog open={!!deleteTarget} onOpenChange={(open) => { if (!open) setDeleteTarget(null); }} title="删除关键词" description={`确定要删除关键词「${deleteTarget?.word_zh}」吗？此操作不可撤销。`} confirmLabel="删除" variant="danger" onConfirm={handleDelete} />
    </div>
  );
}
