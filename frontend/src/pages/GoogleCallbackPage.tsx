/**
 * GoogleCallbackPage — Handles Google OAuth redirect.
 * Extracts tokens from URL hash fragment, stores them, and redirects.
 */

import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { storeTokens } from '@/services/apiClient';
import { useAuth } from '@/store/AuthContext';

export default function GoogleCallbackPage() {
  const navigate = useNavigate();
  const { refreshUser } = useAuth();
  const [error, setError] = useState('');

  useEffect(() => {
    async function handleCallback() {
      const hash = window.location.hash.substring(1);
      const params = new URLSearchParams(hash);
      const accessToken = params.get('access_token');
      const refreshToken = params.get('refresh_token');

      if (accessToken && refreshToken) {
        storeTokens(accessToken, refreshToken);
        await refreshUser();
        navigate('/', { replace: true });
      } else {
        setError('Google authentication failed. Please try again.');
        setTimeout(() => navigate('/login', { replace: true }), 3000);
      }
    }
    handleCallback();
  }, [navigate, refreshUser]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      {error ? (
        <div className="text-center">
          <div className="w-14 h-14 rounded bg-[var(--c-danger-dim)] flex items-center justify-center mx-auto mb-4">
            <span className="material-symbols-outlined text-[var(--c-danger)] text-2xl">error</span>
          </div>
          <p className="text-[var(--c-danger)] font-body text-[14px]">{error}</p>
          <p className="text-[var(--c-text-3)] font-mono text-[11px] mt-2 uppercase tracking-wider">Redirecting to login...</p>
        </div>
      ) : (
        <div className="text-center">
          <span className="material-symbols-outlined text-primary text-3xl animate-spin">progress_activity</span>
          <p className="text-[var(--c-text-2)] font-body text-[13px] mt-4">Completing sign in...</p>
        </div>
      )}
    </div>
  );
}
