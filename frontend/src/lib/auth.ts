/**
 * 认证工具模块
 *
 * - JWT token 的存储、读取、删除
 * - 登录状态检查
 * - 登出与重定向
 */

const TOKEN_KEY = 'auth_token';

/** 获取 JWT token */
export function getToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(TOKEN_KEY);
}

/** 存储 JWT token */
export function setToken(token: string): void {
  if (typeof window === 'undefined') return;
  localStorage.setItem(TOKEN_KEY, token);
}

/** 移除 JWT token */
export function removeToken(): void {
  if (typeof window === 'undefined') return;
  localStorage.removeItem(TOKEN_KEY);
}

/** 检查用户是否已认证（token 是否存在） */
export function isAuthenticated(): boolean {
  return !!getToken();
}

/** 登出：移除 token 并重定向到登录页 */
export function logout(): void {
  removeToken();
  if (typeof window !== 'undefined') {
    window.location.href = '/login';
  }
}
