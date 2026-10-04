import { useState } from 'react';
import { useNavigate, Link, useSearchParams } from 'react-router-dom';
import { useDocumentTitle } from '@/hooks/useDocumentTitle';
import { loginUser, getGoogleLoginUrl } from '@/services/authService';
import { useAuth } from '@/store/AuthContext';

export default function LoginPage() {
  useDocumentTitle('Login — NexusAI');
  const navigate = useNavigate();
  const { refreshUser } = useAuth();
  const [searchParams] = useSearchParams();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(searchParams.get('error') === 'google_auth_failed' ? 'Google sign-in failed. Please try again.' : '');
  const [showPassword, setShowPassword] = useState(false);
  const [showSuccess, setShowSuccess] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const result = await loginUser(email, password);
      if (result.success) {
        await refreshUser();
        setShowSuccess(true);
        setTimeout(() => navigate('/'), 1500);
      } else {
        const msg = result.error?.message ?? 'Login failed.';
        if (msg.toLowerCase().includes('verify your email')) {
          navigate(`/verify-email?email=${encodeURIComponent(email)}`);
          return;
        }
        setError(msg);
      }
    } catch {
      setError('Network error. Please try again.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <div className={`login-success-overlay ${showSuccess ? 'visible' : ''}`}>
        <span className="material-symbols-outlined success-icon">check_circle</span>
        <span className="success-text">Access Granted</span>
      </div>

      <div className="w-full max-w-[380px] mx-auto page-transition">
        {/* Brand */}
        <div className="flex justify-center mb-8">
          <Link to="/" className="no-underline flex items-center gap-2">
            <div className="w-10 h-10 rounded bg-primary/10 flex items-center justify-center">
              <span className="material-symbols-outlined text-primary text-2xl icon-fill">hub</span>
            </div>
          </Link>
        </div>

        <h1 className="font-headline font-bold text-[28px] text-on-surface mb-2 tracking-tight text-center">
          Sign in to NexusAI
        </h1>
        <p className="text-[var(--c-text-2)] text-[13px] font-body text-center mb-8">
          Your AI intelligence command center
        </p>

        {/* Error */}
        {error && (
          <div className="flex items-center gap-2 text-[var(--c-danger)] mb-4 p-3 bg-[var(--c-danger-dim)] rounded border border-[var(--c-danger)]/20">
            <span className="material-symbols-outlined text-base">error</span>
            <span className="font-body text-[13px]">{error}</span>
          </div>
        )}

        {/* Google OAuth */}
        <a
          href={getGoogleLoginUrl()}
          className="w-full py-2.5 rounded font-medium text-[13px] font-body border border-[var(--c-border)] text-on-surface hover:bg-[var(--c-elevated)] transition-colors flex items-center justify-center gap-2.5 no-underline cursor-pointer mb-5"
        >
          <svg width="16" height="16" viewBox="0 0 48 48"><path fill="#4285F4" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"/><path fill="#34A853" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z"/><path fill="#FBBC05" d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z"/><path fill="#EA4335" d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z"/></svg>
          Continue with Google
        </a>

        {/* Divider */}
        <div className="flex items-center gap-3 mb-5">
          <div className="flex-1 h-px bg-[var(--c-border-subtle)]" />
          <span className="font-mono text-[10px] text-[var(--c-text-3)] uppercase tracking-widest">or</span>
          <div className="flex-1 h-px bg-[var(--c-border-subtle)]" />
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="flex flex-col gap-3">
          <div>
            <label className="type-mono-label text-[var(--c-text-3)] mb-1.5 block">Email</label>
            <input
              className="input-field"
              id="login-email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              required
              type="email"
              autoComplete="username"
            />
          </div>
          <div>
            <label className="type-mono-label text-[var(--c-text-3)] mb-1.5 block">Password</label>
            <div className="relative">
              <input
                className="input-field pr-10"
                id="login-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                required
                type={showPassword ? 'text' : 'password'}
                autoComplete="current-password"
              />
              <button
                className="absolute right-2.5 top-1/2 -translate-y-1/2 text-[var(--c-text-3)] hover:text-on-surface bg-transparent border-none cursor-pointer p-0.5"
                type="button"
                onClick={() => setShowPassword(!showPassword)}
              >
                <span className="material-symbols-outlined text-lg">
                  {showPassword ? 'visibility_off' : 'visibility'}
                </span>
              </button>
            </div>
          </div>

          <div className="flex items-center justify-between">
            <div className="remember-me">
              <input type="checkbox" id="remember-me" name="remember-me" />
              <label htmlFor="remember-me">Remember me</label>
            </div>
            <Link
              to="/forgot-password"
              className="text-[12px] font-body text-primary hover:underline no-underline"
            >
              Forgot password?
            </Link>
          </div>

          <button
            disabled={loading}
            className="btn-primary w-full py-2.5 text-[14px] mt-1 btn-press disabled:opacity-50"
            type="submit"
          >
            {loading && <span className="w-4 h-4 border-2 border-transparent border-t-current rounded-full animate-spin" />}
            {loading ? 'Authenticating...' : 'Sign in'}
          </button>
        </form>

        {/* Footer */}
        <p className="mt-8 text-center text-[var(--c-text-2)] font-body text-[13px]">
          Don't have an account?{' '}
          <Link to="/register" className="text-primary font-medium hover:underline no-underline">
            Create account
          </Link>
        </p>
      </div>
    </>
  );
}
