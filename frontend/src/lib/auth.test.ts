import { describe, it, expect, beforeEach, vi } from 'vitest';
import { getToken, setToken, removeToken, isAuthenticated, logout } from './auth';

describe('auth utilities', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  describe('getToken', () => {
    it('returns null when no token is stored', () => {
      expect(getToken()).toBeNull();
    });

    it('returns the stored token', () => {
      localStorage.setItem('auth_token', 'test-jwt-token');
      expect(getToken()).toBe('test-jwt-token');
    });
  });

  describe('setToken', () => {
    it('stores the token in localStorage', () => {
      setToken('my-token');
      expect(localStorage.getItem('auth_token')).toBe('my-token');
    });

    it('overwrites an existing token', () => {
      setToken('old-token');
      setToken('new-token');
      expect(localStorage.getItem('auth_token')).toBe('new-token');
    });
  });

  describe('removeToken', () => {
    it('removes the token from localStorage', () => {
      setToken('to-remove');
      removeToken();
      expect(localStorage.getItem('auth_token')).toBeNull();
    });

    it('does nothing when no token exists', () => {
      removeToken();
      expect(localStorage.getItem('auth_token')).toBeNull();
    });
  });

  describe('isAuthenticated', () => {
    it('returns false when no token is stored', () => {
      expect(isAuthenticated()).toBe(false);
    });

    it('returns true when a token is stored', () => {
      setToken('valid-token');
      expect(isAuthenticated()).toBe(true);
    });

    it('returns false after token is removed', () => {
      setToken('valid-token');
      removeToken();
      expect(isAuthenticated()).toBe(false);
    });
  });

  describe('logout', () => {
    it('removes the token and redirects to /login', () => {
      setToken('session-token');

      // Mock window.location.href
      const hrefSetter = vi.fn();
      Object.defineProperty(window, 'location', {
        value: { href: '' },
        writable: true,
      });
      Object.defineProperty(window.location, 'href', {
        set: hrefSetter,
        get: () => '',
      });

      logout();

      expect(localStorage.getItem('auth_token')).toBeNull();
      expect(hrefSetter).toHaveBeenCalledWith('/login');
    });
  });
});
