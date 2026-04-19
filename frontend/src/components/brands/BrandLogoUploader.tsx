'use client';

import { useState, useRef, useCallback } from 'react';
import clsx from 'clsx';
import { api } from '@/lib/api';
import type { LogoType } from '@/types';

const LOGO_TYPES: Array<{ value: LogoType; label: string }> = [
  { value: 'main', label: '主 Logo' }, { value: 'horizontal', label: '横版 Logo' }, { value: 'icon', label: '图标' }, { value: 'monochrome', label: '单色版' }, { value: 'other', label: '其他' },
];
const ACCEPTED_FORMATS = '.png,.svg,.jpg,.jpeg';

export default function BrandLogoUploader({ brandId, onUploadComplete }: { brandId: string; onUploadComplete: () => void }) {
  const [file, setFile] = useState<File | null>(null);
  const [logoType, setLogoType] = useState<LogoType>('main');
  const [uploading, setUploading] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFile = useCallback((f: File) => {
    const ext = f.name.split('.').pop()?.toLowerCase();
    if (!['png', 'svg', 'jpg', 'jpeg'].includes(ext || '')) { setError('仅支持 PNG、SVG、JPG 格式'); return; }
    setError(null); setFile(f);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => { e.preventDefault(); setDragOver(false); const f = e.dataTransfer.files[0]; if (f) handleFile(f); }, [handleFile]);

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true); setError(null);
    try { const formData = new FormData(); formData.append('file', file); formData.append('logo_type', logoType); await api.post(`/admin/brands/${brandId}/logos`, formData); setFile(null); onUploadComplete(); }
    catch { setError('上传失败，请重试'); }
    finally { setUploading(false); }
  };

  return (
    <div className="mt-3 rounded-lg border border-dashed border-border bg-bg-hover p-4">
      <div onDragOver={(e) => { e.preventDefault(); setDragOver(true); }} onDragLeave={() => setDragOver(false)} onDrop={handleDrop} onClick={() => inputRef.current?.click()}
        className={clsx('flex cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed py-6 transition-colors', dragOver ? 'border-primary/50 bg-primary-bg' : 'border-border hover:border-border-hover')}>
        <svg className="h-6 w-6 text-fg-light" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" /></svg>
        <p className="mt-1.5 text-[13px] text-fg-muted">{file ? file.name : '拖拽文件到此处，或点击选择'}</p>
        <p className="mt-0.5 text-2xs text-fg-light">支持 PNG、SVG、JPG 格式</p>
        <input ref={inputRef} type="file" accept={ACCEPTED_FORMATS} onChange={(e) => { const f = e.target.files?.[0]; if (f) handleFile(f); }} className="hidden" />
      </div>
      {file && (
        <div className="mt-3 flex items-center gap-3">
          <label className="text-[13px] font-medium text-fg-secondary">Logo 类型</label>
          <select value={logoType} onChange={(e) => setLogoType(e.target.value as LogoType)} className="h-7 rounded-lg border border-border bg-white px-2 text-2xs text-fg-secondary focus:outline-none focus:border-primary/50">
            {LOGO_TYPES.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}
          </select>
          <button onClick={handleUpload} disabled={uploading} className="ml-auto h-7 rounded-lg bg-primary px-3 text-2xs font-medium text-white hover:bg-primary-hover disabled:opacity-50">{uploading ? '上传中…' : '上传'}</button>
        </div>
      )}
      {error && <p className="mt-2 text-2xs text-red-500">{error}</p>}
    </div>
  );
}
