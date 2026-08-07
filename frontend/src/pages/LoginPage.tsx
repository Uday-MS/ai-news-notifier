import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useDocumentTitle } from '@/hooks/useDocumentTitle';
import { loginUser } from '@/services/authService';
import { useAuth } from '@/store/AuthContext';

export default function LoginPage() {
  useDocumentTitle('Login — AI News Notifier');
  const navigate = useNavigate();
  const { refreshUser } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
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
        setError(result.error?.message ?? 'Login failed.');
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

      <div className="w-full max-w-[400px] mx-auto page-transition">
        {/* Logo */}
        <div className="flex justify-center mb-8">
          <Link to="/" className="no-underline">
            <span className="material-symbols-outlined text-primary text-4xl icon-fill">hub</span>
          </Link>
        </div>

        <h1 className="text-3xl font-bold text-on-surface mb-8">Sign in to AI News</h1>

        {/* Social Auth */}
        <div className="flex flex-col gap-3 mb-4">
          <button
            type="button"
            className="w-full flex items-center justify-center gap-3 py-2.5 px-4 bg-surface border border-outline rounded-full font-body font-medium text-on-surface hover:bg-surface-container transition-colors cursor-pointer"
          >
            <svg className="w-5 h-5" viewBox="0 0 24 24">
              <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
              <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
              <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
              <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
            </svg>
            Sign in with Google
          </button>
          <button
            type="button"
            className="w-full flex items-center justify-center gap-3 py-2.5 px-4 bg-surface border border-outline rounded-full font-body font-medium text-on-surface hover:bg-surface-container transition-colors cursor-pointer"
          >
            <svg className="w-5 h-5" viewBox="0 0 23 23">
              <path d="M0 0h11v11H0z" fill="#f25022"/><path d="M12 0h11v11H12z" fill="#7fba00"/>
              <path d="M0 12h11v11H0z" fill="#00a4ef"/><path d="M12 12h11v11H12z" fill="#ffb900"/>
            </svg>
            Sign in with Microsoft
          </button>
        </div>

        {/* Divider */}
        <div className="relative my-4">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t border-outline" />
          </div>
          <div className="relative flex justify-center text-sm">
            <span className="px-4 bg-background text-on-surface-variant font-body">or</span>
          </div>
        </div>

        {/* Error */}
        {error && (
          <div className="flex items-center gap-2 text-error mb-4 p-3 bg-error-container rounded-lg">
            <span className="material-symbols-outlined text-lg">error</span>
            <span className="font-body text-sm">{error}</span>
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <div>
            <input
              className="input-field"
              id="login-email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="Email"
              required
              type="email"
              autoComplete="username"
            />
          </div>
          <div className="relative">
            <input
              className="input-field pr-12"
              id="login-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Password"
              required
              type={showPassword ? 'text' : 'password'}
              autoComplete="current-password"
            />
            <button
              className="absolute right-3 top-1/2 -translate-y-1/2 text-on-surface-variant hover:text-on-surface bg-transparent border-none cursor-pointer p-1"
              type="button"
              onClick={() => setShowPassword(!showPassword)}
            >
              <span className="material-symbols-outlined text-xl">
                {showPassword ? 'visibility_off' : 'visibility'}
              </span>
            </button>
          </div>

          <div className="flex items-center justify-between">
            <div className="remember-me">
              <input type="checkbox" id="remember-me" name="remember-me" />
              <label htmlFor="remember-me">Remember me</label>
            </div>
            <Link
              to="/forgot-password"
              className="text-sm font-body text-primary hover:underline no-underline"
            >
              Forgot password?
            </Link>
          </div>

          <button
            disabled={loading}
            className={`w-full bg-primary text-on-primary py-3 rounded-full font-bold text-[15px] font-body hover:opacity-90 transition-opacity border-none cursor-pointer disabled:opacity-50 flex items-center justify-center gap-2 ${loading ? 'opacity-70' : ''}`}
            type="submit"
          >
            {loading && <span className="w-4 h-4 border-2 border-transparent border-t-current rounded-full animate-spin" />}
            {loading ? 'Signing in...' : 'Sign in'}
          </button>
        </form>

        {/* Footer */}
        <p className="mt-10 text-center text-on-surface-variant font-body text-[15px]">
          Don't have an account?{' '}
          <Link to="/register" className="text-primary font-bold hover:underline no-underline">
            Sign up
          </Link>
        </p>
      </div>
    </>
  );
}
