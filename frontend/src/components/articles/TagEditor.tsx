'use client';

import { useState, useCallback } from 'react';
import type { ArticleTag, TagType } from '@/types';
import TagBadge from '@/components/ui/TagBadge';

interface TagEditorProps {
  tags: ArticleTag[];
  onAddTag: (tagType: TagType, tagValue: string) => Promise<void>;
  onRemoveTag: (tagType: TagType, tagValue: string) => Promise<void>;
}

const TAG_TYPE_OPTIONS: { value: TagType; label: string }[] = [
  { value: 'brand', label: '品牌' },
  { value: 'monitor_group', label: '监控组' },
  { value: 'content_type', label: '内容类型' },
  { value: 'keyword', label: '关键词' },
];

export default function TagEditor({ tags, onAddTag, onRemoveTag }: TagEditorProps) {
  const [isAdding, setIsAdding] = useState(false);
  const [newTagType, setNewTagType] = useState<TagType>('keyword');
  const [newTagValue, setNewTagValue] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const handleAdd = useCallback(async () => {
    const trimmed = newTagValue.trim();
    if (!trimmed) return;
    setSubmitting(true);
    try {
      await onAddTag(newTagType, trimmed);
      setNewTagValue('');
      setIsAdding(false);
    } catch {
      // Error handled by parent
    } finally {
      setSubmitting(false);
    }
  }, [newTagType, newTagValue, onAddTag]);

  const handleRemove = useCallback(
    async (tagType: TagType, tagValue: string) => {
      try { await onRemoveTag(tagType, tagValue); } catch { /* parent handles */ }
    },
    [onRemoveTag],
  );

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') { e.preventDefault(); handleAdd(); }
    if (e.key === 'Escape') { setIsAdding(false); setNewTagValue(''); }
  };

  const groupedTags = TAG_TYPE_OPTIONS.map((opt) => ({
    ...opt,
    tags: tags.filter((t) => t.tag_type === opt.value),
  }));

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-[13px] font-medium text-fg">标签</h3>
        {!isAdding && (
          <button
            onClick={() => setIsAdding(true)}
            className="inline-flex items-center gap-1 rounded-md px-2 py-1 text-2xs font-medium text-fg-muted transition-colors hover:bg-bg-hover hover:text-fg-secondary"
          >
            <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
            </svg>
            添加标签
          </button>
        )}
      </div>

      {groupedTags.map(
        (group) =>
          group.tags.length > 0 && (
            <div key={group.value}>
              <p className="mb-1.5 text-2xs text-fg-muted">{group.label}</p>
              <div className="flex flex-wrap gap-1">
                {group.tags.map((tag) => (
                  <TagBadge
                    key={`${tag.tag_type}-${tag.tag_value}`}
                    label={tag.tag_value}
                    variant={tag.tag_type}
                    onRemove={() => handleRemove(tag.tag_type, tag.tag_value)}
                  />
                ))}
              </div>
            </div>
          ),
      )}

      {tags.length === 0 && !isAdding && (
        <p className="text-2xs text-fg-light">暂无标签</p>
      )}

      {isAdding && (
        <div className="flex items-center gap-2 rounded-lg border border-border bg-bg-hover p-2">
          <select
            value={newTagType}
            onChange={(e) => setNewTagType(e.target.value as TagType)}
            className="h-7 rounded-md border border-border bg-white px-2 text-2xs text-fg-secondary focus:outline-none focus:border-primary/50"
            aria-label="标签类型"
          >
            {TAG_TYPE_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
          <input
            type="text"
            value={newTagValue}
            onChange={(e) => setNewTagValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="输入标签值…"
            className="h-7 flex-1 rounded-md border border-border bg-white px-2 text-2xs text-fg placeholder:text-fg-light focus:outline-none focus:border-primary/50"
            autoFocus
            aria-label="标签值"
          />
          <button
            onClick={handleAdd}
            disabled={submitting || !newTagValue.trim()}
            className="h-7 rounded-md bg-primary px-3 text-2xs font-medium text-white transition-colors hover:bg-primary-hover disabled:opacity-50"
          >
            {submitting ? '…' : '添加'}
          </button>
          <button
            onClick={() => { setIsAdding(false); setNewTagValue(''); }}
            className="h-7 rounded-md px-2 text-2xs text-fg-muted transition-colors hover:text-fg"
            aria-label="取消"
          >
            取消
          </button>
        </div>
      )}
    </div>
  );
}
