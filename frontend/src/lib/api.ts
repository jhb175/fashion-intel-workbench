/**
 * 统一 API 客户端
 *
 * - 基于 fetch 的请求封装
 * - 处理后端 JSON 响应格式: {"code": 200, "message": "success", "data": {...}}
 * - 401 错误自动跳转 /login
 * - JWT token 自动附加到 Authorization header
 * - Base URL 通过 NEXT_PUBLIC_API_URL 环境变量配置
 */

import type { ApiResponse } from '@/types';

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

/** 从 localStorage 获取 JWT token */
function getToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('auth_token');
}

/** API 请求错误 */
export class ApiError extends Error {
  constructor(
    public code: number,
    message: string,
    public data?: unknown,
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

/** 构建请求 headers */
function buildHeaders(custom?: HeadersInit): Headers {
  const headers = new Headers(custom);
  if (!headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }
  const token = getToken();
  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }
  return headers;
}

/** 统一请求方法 */
async function request<T>(
  endpoint: string,
  options: RequestInit = {},
): Promise<T> {
  const url = `${BASE_URL}${endpoint}`;

  const headers = buildHeaders(options.headers);
  // 如果是 FormData，删除 Content-Type 让浏览器自动设置 boundary
  if (options.body instanceof FormData) {
    headers.delete('Content-Type');
  }

  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 3000);

  let response: Response;
  try {
    response = await fetch(url, {
      ...options,
      headers,
      signal: controller.signal,
    });
  } catch (err) {
    clearTimeout(timeout);
    if (err instanceof DOMException && err.name === 'AbortError') {
      throw new ApiError(0, '请求超时，后端服务未启动');
    }
    throw new ApiError(0, '网络错误，无法连接到服务器');
  }
  clearTimeout(timeout);

  // 401 未认证 → 跳转登录
  if (response.status === 401) {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('auth_token');
      window.location.href = '/login';
    }
    throw new ApiError(401, '未认证，请重新登录');
  }

  // 解析 JSON 响应
  const json: ApiResponse<T> = await response.json();

  // 业务层错误
  if (json.code !== 200) {
    throw new ApiError(json.code, json.message, json.data);
  }

  return json.data as T;
}

/** API 客户端 */
export const api = {
  get<T>(endpoint: string, params?: Record<string, string>): Promise<T> {
    const query = params ? `?${new URLSearchParams(params).toString()}` : '';
    return request<T>(`${endpoint}${query}`, { method: 'GET' });
  },

  post<T>(endpoint: string, body?: unknown): Promise<T> {
    return request<T>(endpoint, {
      method: 'POST',
      body: body instanceof FormData ? body : JSON.stringify(body),
    });
  },

  put<T>(endpoint: string, body?: unknown): Promise<T> {
    return request<T>(endpoint, {
      method: 'PUT',
      body: JSON.stringify(body),
    });
  },

  patch<T>(endpoint: string, body?: unknown): Promise<T> {
    return request<T>(endpoint, {
      method: 'PATCH',
      body: JSON.stringify(body),
    });
  },

  delete<T>(endpoint: string): Promise<T> {
    return request<T>(endpoint, { method: 'DELETE' });
  },
};
