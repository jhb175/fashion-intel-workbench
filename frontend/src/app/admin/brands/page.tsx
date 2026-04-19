'use client';

import { useState, useEffect, useCallback } from 'react';
import { api } from '@/lib/api';
import type { Brand, MonitorGroup, PaginatedData } from '@/types';
import PageHeader from '@/components/layout/PageHeader';
import LoadingSpinner from '@/components/ui/LoadingSpinner';
import ErrorMessage from '@/components/ui/ErrorMessage';
import EmptyState from '@/components/ui/EmptyState';
import Pagination from '@/components/ui/Pagination';
import ConfirmDialog from '@/components/ui/ConfirmDialog';
import BrandNamingSearch from '@/components/brands/BrandNamingSearch';
import BrandLogoGallery from '@/components/brands/BrandLogoGallery';

const PAGE_SIZE = 15;
interface BrandFormData { name_zh: string; name_en: string; monitor_group_id: string; official_name: string; social_media_name: string; naming_notes: string; }
const emptyForm: BrandFormData = { name_zh: '', name_en: '', monitor_group_id: '', official_name: '', social_media_name: '', naming_notes: '' };

export default function AdminBrandsPage() {
  const [brands, setBrands] = useState<Brand[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [monitorGroups, setMonitorGroups] = useState<MonitorGroup[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [form, setForm] = useState<BrandFormData>(emptyForm);
  const [saving, setSaving] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<Brand | null>(null);
  const [expandedBrandId, setExpandedBrandId] = useState<string | null>(null);

  useEffect(() => { api.get<MonitorGroup[] | { items: MonitorGroup[] }>('/admin/monitor-groups').then((res) => { setMonitorGroups(Array.isArray(res) ? res : (res as { items: MonitorGroup[] }).items || []); }).catch(() => {}); }, []);

  const fetchBrands = useCallback(async () => {
    setLoading(true); setError(null);
    try { const data = await api.get<PaginatedData<Brand>>('/admin/brands', { page: String(page), page_size: String(PAGE_SIZE) }); setBrands(data.items); setTotal(data.total); }
    catch { setError('加载品牌列表失败'); } finally { setLoading(false); }
  }, [page]);

  useEffect(() => { fetchBrands(); }, [fetchBrands]);

  const groupName = (groupId: string) => monitorGroups.find((g) => g.id === groupId)?.display_name || groupId;
  const openAdd = () => { setEditingId(null); setForm({ ...emptyForm, monitor_group_id: monitorGroups[0]?.id || '' }); setShowForm(true); };
  const openEdit = (brand: Brand) => { setEditingId(brand.id); setForm({ name_zh: brand.name_zh, name_en: brand.name_en, monitor_group_id: brand.monitor_group_id, official_name: brand.official_name || '', social_media_name: brand.social_media_name || '', naming_notes: brand.naming_notes || '' }); setShowForm(true); };
  const handleSave = async () => { setSaving(true); try { if (editingId) { await api.put(`/admin/brands/${editingId}`, form); } else { await api.post('/admin/brands', form); } setShowForm(false); fetchBrands(); } catch {} finally { setSaving(false); } };
  const handleDelete = async () => { if (!deleteTarget) return; try { await api.delete(`/admin/brands/${deleteTarget.id}`); setDeleteTarget(null); fetchBrands(); } catch { setDeleteTarget(null); } };
  const updateField = (field: keyof BrandFormData, value: string) => setForm((prev) => ({ ...prev, [field]: value }));

  return (
    <div className="space-y-6 pb-12">
      <PageHeader title="品牌池管理" breadcrumbs={[{ label: '首页', href: '/' }, { label: '后台管理' }, { label: '品牌池管理' }]}
        actions={<button onClick={openAdd} className="h-8 rounded-lg bg-primary px-3 text-[13px] font-medium text-white hover:bg-primary-hover">+ 添加品牌</button>} />

      <BrandNamingSearch className="mb-4" />

      {showForm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60" onClick={() => setShowForm(false)}>
          <div className="w-full max-w-lg rounded-lg border border-border bg-white p-6 shadow-panel" onClick={(e) => e.stopPropagation()}>
            <h2 className="text-[14px] font-medium text-fg">{editingId ? '编辑品牌' : '添加品牌'}</h2>
            <div className="mt-4 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div><label className="block text-[13px] font-medium text-fg-secondary">中文名</label><input value={form.name_zh} onChange={(e) => updateField('name_zh', e.target.value)} className="mt-1 h-8 w-full rounded-lg border border-border bg-bg px-3 text-[13px] text-fg focus:border-primary/50 focus:outline-none focus:ring-1 focus:ring-primary/20" /></div>
                <div><label className="block text-[13px] font-medium text-fg-secondary">英文名</label><input value={form.name_en} onChange={(e) => updateField('name_en', e.target.value)} className="mt-1 h-8 w-full rounded-lg border border-border bg-bg px-3 text-[13px] text-fg focus:border-primary/50 focus:outline-none focus:ring-1 focus:ring-primary/20" /></div>
              </div>
              <div><label className="block text-[13px] font-medium text-fg-secondary">监控组</label><select value={form.monitor_group_id} onChange={(e) => updateField('monitor_group_id', e.target.value)} className="mt-1 h-8 w-full rounded-lg border border-border bg-bg px-3 text-[13px] text-fg focus:border-primary/50 focus:outline-none focus:ring-1 focus:ring-primary/20">{monitorGroups.map((g) => <option key={g.id} value={g.id}>{g.display_name}</option>)}</select></div>
              <div className="border-t border-border pt-4"><p className="text-2xs font-medium text-fg-muted">品牌写法信息</p></div>
              <div><label className="block text-[13px] font-medium text-fg-secondary">官方英文写法</label><input value={form.official_name} onChange={(e) => updateField('official_name', e.target.value)} className="mt-1 h-8 w-full rounded-lg border border-border bg-bg px-3 text-[13px] text-fg focus:border-primary/50 focus:outline-none focus:ring-1 focus:ring-primary/20" placeholder='如 "LOUIS VUITTON"、"adidas"' /></div>
              <div><label className="block text-[13px] font-medium text-fg-secondary">社交媒体写法</label><input value={form.social_media_name} onChange={(e) => updateField('social_media_name', e.target.value)} className="mt-1 h-8 w-full rounded-lg border border-border bg-bg px-3 text-[13px] text-fg focus:border-primary/50 focus:outline-none focus:ring-1 focus:ring-primary/20" placeholder="社交媒体常用写法" /></div>
              <div><label className="block text-[13px] font-medium text-fg-secondary">写法备注</label><textarea value={form.naming_notes} onChange={(e) => updateField('naming_notes', e.target.value)} rows={2} className="mt-1 w-full rounded-lg border border-border bg-bg px-3 py-2 text-[13px] text-fg focus:border-primary/50 focus:outline-none focus:ring-1 focus:ring-primary/20" placeholder='如"全大写"、"全小写"、"含™符号"' /></div>
            </div>
            <div className="mt-6 flex justify-end gap-2">
              <button onClick={() => setShowForm(false)} className="h-8 rounded-lg border border-border bg-white px-3 text-[13px] font-medium text-fg-secondary hover:bg-bg-hover">取消</button>
              <button onClick={handleSave} disabled={saving || !form.name_zh || !form.name_en} className="h-8 rounded-lg bg-primary px-3 text-[13px] font-medium text-white hover:bg-primary-hover disabled:opacity-50">{saving ? '保存中…' : '保存'}</button>
            </div>
          </div>
        </div>
      )}

      {loading ? (
        <div className="flex min-h-[40vh] items-center justify-center"><LoadingSpinner size="lg" label="加载品牌列表中…" /></div>
      ) : error ? (
        <ErrorMessage message={error} onRetry={fetchBrands} />
      ) : brands.length === 0 ? (
        <EmptyState title="暂无品牌" description="点击上方按钮添加第一个品牌" action={<button onClick={openAdd} className="h-8 rounded-lg bg-primary px-3 text-[13px] font-medium text-white hover:bg-primary-hover">添加品牌</button>} />
      ) : (
        <>
          <p className="text-2xs text-fg-muted">共 <span className="font-medium text-fg-secondary">{total}</span> 个品牌</p>
          <div className="space-y-3">
            {brands.map((brand) => (
              <div key={brand.id} className="rounded-lg border border-border bg-white shadow-card transition-shadow hover:shadow-card-hover">
                <div className="flex items-center gap-4 px-4 py-3">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-[13px] text-fg">{brand.name_zh}</span>
                      <span className="text-[13px] text-fg-muted">{brand.name_en}</span>
                    </div>
                    <div className="mt-1 flex flex-wrap items-center gap-2 text-2xs text-fg-muted">
                      <span>{groupName(brand.monitor_group_id)}</span>
                      {brand.official_name && <span className="rounded-md border border-amber-200 bg-amber-50 px-1.5 py-0.5 text-amber-700">{brand.official_name}</span>}
                      {brand.social_media_name && <span className="text-fg-light">社媒: {brand.social_media_name}</span>}
                    </div>
                    {brand.naming_notes && <p className="mt-0.5 text-2xs text-fg-light italic">{brand.naming_notes}</p>}
                  </div>
                  <div className="flex items-center gap-1">
                    <button onClick={() => setExpandedBrandId(expandedBrandId === brand.id ? null : brand.id)} className="rounded-md px-2 py-1 text-2xs font-medium text-fg-secondary transition-colors hover:bg-bg-hover">{expandedBrandId === brand.id ? '收起 Logo' : 'Logo'}</button>
                    <button onClick={() => openEdit(brand)} className="rounded-md px-2 py-1 text-2xs font-medium text-fg-secondary transition-colors hover:bg-bg-hover">编辑</button>
                    <button onClick={() => setDeleteTarget(brand)} className="rounded-md px-2 py-1 text-2xs font-medium text-red-500 transition-colors hover:bg-red-50">删除</button>
                  </div>
                </div>
                {expandedBrandId === brand.id && (
                  <div className="border-t border-border px-4 py-3">
                    <BrandLogoGallery brandId={brand.id} />
                  </div>
                )}
              </div>
            ))}
          </div>
          <Pagination page={page} total={total} pageSize={PAGE_SIZE} onPageChange={(p) => { setPage(p); window.scrollTo({ top: 0, behavior: 'smooth' }); }} className="mt-6" />
        </>
      )}

      <ConfirmDialog open={!!deleteTarget} onOpenChange={(open) => { if (!open) setDeleteTarget(null); }} title="删除品牌" description={`确定要删除品牌「${deleteTarget?.name_zh}」吗？关联的 Logo 文件也将被删除。此操作不可撤销。`} confirmLabel="删除" variant="danger" onConfirm={handleDelete} />
    </div>
  );
}
