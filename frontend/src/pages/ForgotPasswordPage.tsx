import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useDocumentTitle } from '@/hooks/useDocumentTitle';
import { forgotPassword } from '@/services/authService';

export default function ForgotPasswordPage() {
  useDocumentTitle('Forgot Password — NexusAI');
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);
  const [error, setError] = useState('');

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault(); setError(''); setLoading(true);
    try {
      const result = await forgotPassword(email);
      if (result.success) setSent(true);
      else setError(result.error?.message ?? 'Request failed.');
    } catch { setError('Network error. Please try again.'); }
    finally { setLoading(false); }
  }

  return (
    <div className="w-full max-w-[380px] mx-auto page-transition">
      <div className="flex justify-center mb-8">
        <Link to="/" className="no-underline">
          <div className="w-10 h-10 rounded bg-primary/10 flex items-center justify-center">
            <span className="material-symbols-outlined text-primary text-2xl icon-fill">hub</span>
          </div>
        </Link>
      </div>

      {sent ? (
        <div className="text-center">
          <div className="w-14 h-14 rounded bg-[var(--c-tertiary-dim)] flex items-center justify-center mx-auto mb-4">
            <span className="material-symbols-outlined text-3xl text-[var(--c-tertiary)]">mark_email_read</span>
          </div>
          <h1 className="font-headline font-bold text-[28px] text-on-surface mb-2 tracking-tight">Check your email</h1>
          <p className="text-[var(--c-text-2)] text-[13px] font-body mb-8">If an account with this email exists, a reset link has been sent.</p>
          <Link to="/login" className="btn-primary inline-flex py-2.5 px-6 text-[14px] no-underline">Back to sign in</Link>
        </div>
      ) : (
        <>
          <h1 className="font-headline font-bold text-[28px] text-on-surface mb-2 tracking-tight text-center">Find your account</h1>
          <p className="text-[var(--c-text-2)] text-[13px] font-body text-center mb-8">Enter the email associated with your account.</p>

          {error && (
            <div className="flex items-center gap-2 text-[var(--c-danger)] mb-4 p-3 bg-[var(--c-danger-dim)] rounded border border-[var(--c-danger)]/20">
              <span className="material-symbols-outlined text-base">error</span>
              <span className="font-body text-[13px]">{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="flex flex-col gap-3">
            <div>
              <label className="type-mono-label text-[var(--c-text-3)] mb-1.5 block">Email</label>
              <input className="input-field" id="fp-email" value={email} onChange={(e) => setEmail(e.target.value)} required type="email" placeholder="you@example.com" />
            </div>
            <button disabled={loading} className="btn-primary w-full py-2.5 text-[14px] mt-1 btn-press disabled:opacity-50" type="submit">
              {loading && <span className="w-4 h-4 border-2 border-transparent border-t-current rounded-full animate-spin" />}
              {loading ? 'Sending...' : 'Send reset link'}
            </button>
          </form>

          <p className="mt-8 text-center">
            <Link to="/login" className="text-primary font-body text-[13px] hover:underline no-underline">← Back to sign in</Link>
          </p>
        </>
      )}
    </div>
  );
}
