'use client';

import { useState, useEffect, useCallback } from 'react';
import clsx from 'clsx';
import { api } from '@/lib/api';
import type { KnowledgeEntry, PaginatedData } from '@/types';
import PageHeader from '@/components/layout/PageHeader';
import LoadingSpinner from '@/components/ui/LoadingSpinner';
import ErrorMessage from '@/components/ui/ErrorMessage';
import Pagination from '@/components/ui/Pagination';
import SearchInput from '@/components/ui/SearchInput';
import ConfirmDialog from '@/components/ui/ConfirmDialog';
import KnowledgeGrid from '@/components/knowledge/KnowledgeGrid';
import KnowledgeEditor from '@/components/knowledge/KnowledgeEditor';
import type { KnowledgeFormData } from '@/components/knowledge/KnowledgeEditor';

const PAGE_SIZE = 12;

const CATEGORY_TABS: Array<{ value: string; label: string }> = [
  { value: '', label: '全部' },
  { value: 'brand_profile', label: '品牌档案' },
  { value: 'style_history', label: '风格历史' },
  { value: 'classic_item', label: '经典单品' },
  { value: 'person_profile', label: '人物档案' },
];

export default function KnowledgePage() {
  const [entries, setEntries] = useState<KnowledgeEntry[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [category, setCategory] = useState('');
  const [keyword, setKeyword] = useState('');
  const [debouncedKeyword, setDebouncedKeyword] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showEditor, setShowEditor] = useState(false);
  const [editingEntry, setEditingEntry] = useState<KnowledgeEntry | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<KnowledgeEntry | null>(null);

  useEffect(() => { const timer = setTimeout(() => setDebouncedKeyword(keyword), 400); return () => clearTimeout(timer); }, [keyword]);
  useEffect(() => { setPage(1); }, [category, debouncedKeyword]);

  const fetchEntries = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params: Record<string, string> = { page: String(page), page_size: String(PAGE_SIZE) };
      if (category) params.category = category;
      if (debouncedKeyword) params.keyword = debouncedKeyword;
      const data = await api.get<PaginatedData<KnowledgeEntry>>('/knowledge', params);
      setEntries(data.items);
      setTotal(data.total);
    } catch { setError('加载知识库失败，请稍后重试'); }
    finally { setLoading(false); }
  }, [page, category, debouncedKeyword]);

  useEffect(() => { fetchEntries(); }, [fetchEntries]);

  const handlePageChange = (newPage: number) => { setPage(newPage); window.scrollTo({ top: 0, behavior: 'smooth' }); };
  const openCreate = () => { setEditingEntry(null); setShowEditor(true); };
  const openEdit = (entry: KnowledgeEntry) => { setEditingEntry(entry); setShowEditor(true); };

  const handleEditorSubmit = async (data: KnowledgeFormData) => {
    if (editingEntry) { await api.put(`/knowledge/${editingEntry.id}`, data); }
    else { await api.post('/knowledge', data); }
    setShowEditor(false);
    setEditingEntry(null);
    fetchEntries();
  };

  const handleDelete = async () => {
    if (!deleteTarget) return;
    try { await api.delete(`/knowledge/${deleteTarget.id}`); setDeleteTarget(null); fetchEntries(); }
    catch { setDeleteTarget(null); }
  };

  return (
    <div className="space-y-6 pb-12">
      <PageHeader title="知识库" breadcrumbs={[{ label: '首页', href: '/' }, { label: '知识库' }]}
        actions={<button onClick={openCreate} className="h-8 rounded-lg bg-primary px-3 text-[13px] font-medium text-white transition-colors hover:bg-primary-hover">+ 创建条目</button>}
      />

      {showEditor && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60" onClick={() => { setShowEditor(false); setEditingEntry(null); }}>
          <KnowledgeEditor initialData={editingEntry || undefined} onSubmit={handleEditorSubmit} onCancel={() => { setShowEditor(false); setEditingEntry(null); }} />
        </div>
      )}

      <div className="space-y-3">
        <SearchInput value={keyword} onChange={setKeyword} placeholder="搜索知识条目…" className="max-w-md" />
        <div className="flex items-center gap-0.5 rounded-lg border border-border bg-white p-0.5 w-fit">
          {CATEGORY_TABS.map((tab) => (
            <button key={tab.value} onClick={() => setCategory(tab.value)}
              className={clsx('rounded-md px-2.5 py-1 text-2xs font-medium transition-colors', category === tab.value ? 'bg-bg-active text-fg' : 'text-fg-muted hover:text-fg-secondary')}>
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <div className="flex min-h-[40vh] items-center justify-center"><LoadingSpinner size="lg" label="加载知识库中…" /></div>
      ) : error ? (
        <ErrorMessage message={error} onRetry={fetchEntries} />
      ) : (
        <>
          <p className="text-2xs text-fg-muted">共 <span className="font-medium text-fg-secondary">{total}</span> 条知识条目</p>
          <KnowledgeGrid entries={entries} onEdit={openEdit} onDelete={setDeleteTarget} />
          <Pagination page={page} total={total} pageSize={PAGE_SIZE} onPageChange={handlePageChange} className="mt-6" />
        </>
      )}

      <ConfirmDialog open={!!deleteTarget} onOpenChange={(open) => { if (!open) setDeleteTarget(null); }}
        title="删除知识条目" description={`确定要删除知识条目「${deleteTarget?.title}」吗？此操作不可撤销。`}
        confirmLabel="删除" variant="danger" onConfirm={handleDelete} />
    </div>
  );
}
