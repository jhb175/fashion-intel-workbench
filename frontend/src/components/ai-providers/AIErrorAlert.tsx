'use client';

import type { AIErrorType } from '@/types';

const errorConfig: Record<AIErrorType, { title: string; suggestion: string; color: string }> = {
  auth_failed: { title: '认证失败', suggestion: '请检查 API Key 是否正确，或是否已过期。', color: 'border-red-200 bg-red-50 text-red-600' },
  quota_exceeded: { title: '配额不足', suggestion: '请检查 API 账户余额，或稍后重试。', color: 'border-amber-200 bg-amber-50 text-amber-700' },
  network_timeout: { title: '网络超时', suggestion: '请检查网络连接或 API URL 是否正确。', color: 'border-orange-200 bg-orange-50 text-orange-700' },
  model_not_found: { title: '模型不存在', suggestion: '请检查模型名称是否正确。', color: 'border-purple-200 bg-purple-50 text-purple-700' },
  server_error: { title: '服务暂时不可用', suggestion: '请稍后重试。', color: 'border-border bg-bg-hover text-fg-secondary' },
};

export default function AIErrorAlert({ errorType, errorMessage, className }: { errorType: AIErrorType; errorMessage?: string; className?: string }) {
  const config = errorConfig[errorType] || errorConfig.server_error;

  return (
    <div className={`rounded-lg border p-3 ${config.color} ${className || ''}`}>
      <div className="flex items-start gap-2">
        <svg className="mt-0.5 h-3.5 w-3.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
        </svg>
        <div>
          <p className="text-[13px] font-medium">{config.title}</p>
          {errorMessage && <p className="mt-0.5 text-2xs opacity-80">{errorMessage}</p>}
          <p className="mt-1 text-2xs opacity-70">{config.suggestion}</p>
        </div>
      </div>
    </div>
  );
}
