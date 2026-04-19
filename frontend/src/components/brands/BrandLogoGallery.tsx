'use client';

import { useState, useEffect, useCallback } from 'react';
import clsx from 'clsx';
import { api } from '@/lib/api';
import type { BrandLogo } from '@/types';
import BrandLogoCard from '@/components/brands/BrandLogoCard';
import BrandLogoUploader from '@/components/brands/BrandLogoUploader';
import LoadingSpinner from '@/components/ui/LoadingSpinner';

const LOGO_TYPE_FILTERS: Array<{ value: string; label: string }> = [
  { value: '', label: '全部' }, { value: 'main', label: '主 Logo' }, { value: 'horizontal', label: '横版' }, { value: 'icon', label: '图标' }, { value: 'monochrome', label: '单色版' }, { value: 'other', label: '其他' },
];

export default function BrandLogoGallery({ brandId, className }: { brandId: string; className?: string }) {
  const [logos, setLogos] = useState<BrandLogo[]>([]);
  const [loading, setLoading] = useState(true);
  const [typeFilter, setTypeFilter] = useState('');
  const [showUploader, setShowUploader] = useState(false);

  const fetchLogos = useCallback(async () => {
    setLoading(true);
    try { const res = await api.get<BrandLogo[] | { items: BrandLogo[] }>(`/admin/brands/${brandId}/logos`); setLogos(Array.isArray(res) ? res : (res as { items: BrandLogo[] }).items || []); }
    catch { setLogos([]); }
    finally { setLoading(false); }
  }, [brandId]);

  useEffect(() => { fetchLogos(); }, [fetchLogos]);

  const filteredLogos = typeFilter ? logos.filter((l) => l.logo_type === typeFilter) : logos;

  const handleDelete = async (logoId: string) => { try { await api.delete(`/admin/brands/${brandId}/logos/${logoId}`); setLogos((prev) => prev.filter((l) => l.id !== logoId)); } catch {} };
  const handleDownload = (logoId: string, fileName: string) => { const url = `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'}/admin/brands/${brandId}/logos/${logoId}/download`; const a = document.createElement('a'); a.href = url; a.download = fileName; a.click(); };
  const handleUploadComplete = () => { setShowUploader(false); fetchLogos(); };

  return (
    <div className={className}>
      <div className="flex items-center justify-between">
        <h3 className="text-[13px] font-medium text-fg">Logo 文件</h3>
        <button onClick={() => setShowUploader(!showUploader)} className="h-7 rounded-lg bg-primary px-3 text-2xs font-medium text-white hover:bg-primary-hover">{showUploader ? '取消上传' : '+ 上传 Logo'}</button>
      </div>
      <div className="mt-2 flex items-center gap-0.5 rounded-lg border border-border bg-white p-0.5 w-fit">
        {LOGO_TYPE_FILTERS.map((f) => (
          <button key={f.value} onClick={() => setTypeFilter(f.value)} className={clsx('rounded-md px-2 py-1 text-2xs font-medium transition-colors', typeFilter === f.value ? 'bg-bg-active text-fg' : 'text-fg-muted hover:text-fg-secondary')}>{f.label}</button>
        ))}
      </div>
      {showUploader && <BrandLogoUploader brandId={brandId} onUploadComplete={handleUploadComplete} />}
      {loading ? (
        <div className="mt-4 flex justify-center py-6"><LoadingSpinner size="sm" /></div>
      ) : filteredLogos.length === 0 ? (
        <p className="mt-4 text-center text-2xs text-fg-light py-6">暂无 Logo 文件</p>
      ) : (
        <div className="mt-3 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
          {filteredLogos.map((logo) => <BrandLogoCard key={logo.id} logo={logo} onDelete={() => handleDelete(logo.id)} onDownload={() => handleDownload(logo.id, logo.file_name)} />)}
        </div>
      )}
    </div>
  );
}
