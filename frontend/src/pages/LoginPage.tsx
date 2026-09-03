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
