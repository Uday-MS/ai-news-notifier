import { useState } from 'react';
import { Link, useSearchParams, useNavigate } from 'react-router-dom';
import { useDocumentTitle } from '@/hooks/useDocumentTitle';
import { resetPassword } from '@/services/authService';

export default function ResetPasswordPage() {
  useDocumentTitle('Reset Password — AI News Notifier');
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token') ?? '';
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError('');

    if (password !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }

    setLoading(true);
    try {
      const result = await resetPassword(token, password);
      if (result.success) {
        setSuccess(true);
        setTimeout(() => navigate('/login'), 2000);
      } else {
        setError(result.error?.message ?? 'Reset failed.');
      }
    } catch {
      setError('Network error. Please try again.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="w-full max-w-[400px] mx-auto page-transition">
      {/* Logo */}
      <div className="flex justify-center mb-8">
        <Link to="/" className="no-underline">
          <span className="material-symbols-outlined text-primary text-4xl icon-fill">hub</span>
        </Link>
      </div>

      {success ? (
        <div className="text-center">
          <span className="material-symbols-outlined text-6xl text-primary mb-4 block">lock_reset</span>
          <h1 className="text-3xl font-bold text-on-surface mb-3">Password reset</h1>
          <p className="text-on-surface-variant font-body mb-8">
            Your password has been updated. Redirecting to login...
          </p>
        </div>
      ) : (
        <>
          <h1 className="text-3xl font-bold text-on-surface mb-2">Reset your password</h1>
          <p className="text-on-surface-variant font-body mb-6">Enter your new password below.</p>

          {error && (
            <div className="flex items-center gap-2 text-error mb-4 p-3 bg-error-container rounded-lg">
              <span className="material-symbols-outlined text-lg">error</span>
              <span className="font-body text-sm">{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            <input
              className="input-field"
              id="new-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              type="password"
              placeholder="New password"
            />
            <input
              className="input-field"
              id="rp-confirm"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
              type="password"
              placeholder="Confirm new password"
            />
            <button
              disabled={loading}
              className="w-full bg-primary text-on-primary py-3 rounded-full font-bold text-[15px] font-body hover:opacity-90 transition-opacity border-none cursor-pointer disabled:opacity-50 flex items-center justify-center gap-2"
              type="submit"
            >
              {loading && <span className="w-4 h-4 border-2 border-transparent border-t-current rounded-full animate-spin" />}
              {loading ? 'Resetting...' : 'Reset password'}
            </button>
          </form>
        </>
      )}
    </div>
  );
}
