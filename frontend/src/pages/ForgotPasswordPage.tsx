import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useDocumentTitle } from '@/hooks/useDocumentTitle';
import { forgotPassword } from '@/services/authService';

export default function ForgotPasswordPage() {
  useDocumentTitle('Forgot Password — AI News Notifier');
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);
  const [error, setError] = useState('');

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const result = await forgotPassword(email);
      if (result.success) {
        setSent(true);
      } else {
        setError(result.error?.message ?? 'Request failed.');
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

      {sent ? (
        <div className="text-center">
          <span className="material-symbols-outlined text-6xl text-primary mb-4 block">mark_email_read</span>
          <h1 className="text-3xl font-headline text-on-surface mb-3">Check your email</h1>
          <p className="text-on-surface-variant font-body mb-8">
            If an account with this email exists, a reset link has been sent.
          </p>
          <Link
            to="/login"
            className="inline-block bg-primary text-on-primary py-3 px-8 rounded-full font-bold text-[15px] font-body hover:opacity-90 transition-opacity no-underline"
          >
            Back to sign in
          </Link>
        </div>
      ) : (
        <>
          <h1 className="text-3xl font-headline text-on-surface mb-2">Find your account</h1>
          <p className="text-on-surface-variant font-body mb-6">
            Enter the email associated with your account to reset your password.
          </p>

          {error && (
            <div className="flex items-center gap-2 text-error mb-4 p-3 bg-error-container rounded-lg">
              <span className="material-symbols-outlined text-lg">error</span>
              <span className="font-body text-sm">{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            <input
              className="input-field"
              id="fp-email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              type="email"
              placeholder="Email"
            />
            <button
              disabled={loading}
              className="w-full bg-primary text-on-primary py-3 rounded-full font-bold text-[15px] font-body hover:opacity-90 transition-opacity border-none cursor-pointer disabled:opacity-50 flex items-center justify-center gap-2"
              type="submit"
            >
              {loading && <span className="w-4 h-4 border-2 border-transparent border-t-current rounded-full animate-spin" />}
              {loading ? 'Sending...' : 'Send reset link'}
            </button>
          </form>

          <p className="mt-8 text-center">
            <Link to="/login" className="text-primary font-body text-sm hover:underline no-underline">
              ← Back to sign in
            </Link>
          </p>
        </>
      )}
    </div>
  );
}
