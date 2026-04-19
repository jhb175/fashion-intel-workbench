'use client';

import { useState } from 'react';
import { api } from '@/lib/api';
import type { ConnectionTestResult, AIErrorType } from '@/types';
import AIErrorAlert from '@/components/ai-providers/AIErrorAlert';

interface ConnectionTestButtonProps { providerId: string; onTestComplete?: (result: ConnectionTestResult) => void; }

export default function ConnectionTestButton({ providerId, onTestComplete }: ConnectionTestButtonProps) {
  const [testing, setTesting] = useState(false);
  const [result, setResult] = useState<ConnectionTestResult | null>(null);

  const handleTest = async () => {
    setTesting(true); setResult(null);
    try { const res = await api.post<ConnectionTestResult>(`/ai-providers/${providerId}/test`); setResult(res); onTestComplete?.(res); }
    catch { setResult({ status: 'failed', error_type: 'network_timeout', error_message: '请求失败，请检查网络连接' }); }
    finally { setTesting(false); }
  };

  return (
    <div>
      <button onClick={handleTest} disabled={testing}
        className="inline-flex items-center gap-1.5 h-7 rounded-lg border border-border bg-white px-3 text-2xs font-medium text-fg-secondary transition-colors hover:bg-bg-hover disabled:opacity-50">
        {testing ? (
          <><svg className="h-3 w-3 animate-spin" viewBox="0 0 24 24" fill="none"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" /><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" /></svg>测试中…</>
        ) : (
          <><svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M5.636 18.364a9 9 0 010-12.728m12.728 0a9 9 0 010 12.728m-9.9-2.829a5 5 0 010-7.07m7.072 0a5 5 0 010 7.07M13 12a1 1 0 11-2 0 1 1 0 012 0z" /></svg>测试连接</>
        )}
      </button>
      {result && (
        <div className="mt-2">
          {result.status === 'success' ? (
            <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-3">
              <div className="flex items-center gap-2">
                <svg className="h-3.5 w-3.5 text-emerald-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                <span className="text-[13px] font-medium text-emerald-600">连接成功</span>
              </div>
              <div className="mt-1 flex items-center gap-3 text-2xs text-emerald-600/70">
                {result.response_time_ms && <span>响应时间: {result.response_time_ms}ms</span>}
                {result.model_info && <span>模型: {result.model_info}</span>}
              </div>
            </div>
          ) : (
            <AIErrorAlert errorType={result.error_type as AIErrorType || 'server_error'} errorMessage={result.error_message} />
          )}
        </div>
      )}
    </div>
  );
}
