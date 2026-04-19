'use client';

import type { AIProvider } from '@/types';
import AIProviderCard from '@/components/ai-providers/AIProviderCard';

interface AIProviderListProps {
  providers: AIProvider[];
  onEdit: (provider: AIProvider) => void;
  onDelete: (provider: AIProvider) => void;
  onActivate: (provider: AIProvider) => void;
  onRefresh: () => void;
}

export default function AIProviderList({ providers, onEdit, onDelete, onActivate, onRefresh }: AIProviderListProps) {
  const sorted = [...providers].sort((a, b) => {
    if (a.is_active !== b.is_active) return a.is_active ? -1 : 1;
    if (a.is_preset !== b.is_preset) return a.is_preset ? -1 : 1;
    return a.name.localeCompare(b.name);
  });

  return (
    <div className="grid gap-3 sm:grid-cols-2">
      {sorted.map((provider) => (
        <AIProviderCard key={provider.id} provider={provider} onEdit={() => onEdit(provider)} onDelete={() => onDelete(provider)} onActivate={() => onActivate(provider)} onTestComplete={onRefresh} />
      ))}
    </div>
  );
}
