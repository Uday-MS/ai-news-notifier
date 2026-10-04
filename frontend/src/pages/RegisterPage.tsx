import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useDocumentTitle } from '@/hooks/useDocumentTitle';
import { registerUser } from '@/services/authService';

export default function RegisterPage() {
  useDocumentTitle('Sign up — NexusAI');
  const navigate = useNavigate();
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError('');
    if (password !== confirmPassword) { setError('Passwords do not match.'); return; }
    setLoading(true);
    try {
      const result = await registerUser(email, password, fullName);
      if (result.success) {
        setSuccess(true);
        setTimeout(() => navigate(`/verify-email?email=${encodeURIComponent(email)}`), 2000);
      } else {
        setError(result.error?.message ?? 'Registration failed.');
      }
    } catch { setError('Network error. Please try again.'); }
    finally { setLoading(false); }
  }

  return (
    <div className="w-full max-w-[380px] mx-auto page-transition">
      {/* Brand */}
      <div className="flex justify-center mb-8">
        <Link to="/" className="no-underline">
          <div className="w-10 h-10 rounded bg-primary/10 flex items-center justify-center">
            <span className="material-symbols-outlined text-primary text-2xl icon-fill">hub</span>
          </div>
        </Link>
      </div>

      <h1 className="font-headline font-bold text-[28px] text-on-surface mb-2 tracking-tight text-center">
        Create your account
      </h1>
      <p className="text-[var(--c-text-2)] text-[13px] font-body text-center mb-8">
        Join the AI intelligence network
      </p>

      {error && (
        <div className="flex items-center gap-2 text-[var(--c-danger)] mb-4 p-3 bg-[var(--c-danger-dim)] rounded border border-[var(--c-danger)]/20">
          <span className="material-symbols-outlined text-base">error</span>
          <span className="font-body text-[13px]">{error}</span>
        </div>
      )}

      {success && (
        <div className="flex items-center gap-2 text-[var(--c-tertiary)] mb-4 p-3 bg-[var(--c-tertiary-dim)] rounded border border-[var(--c-tertiary)]/20">
          <span className="material-symbols-outlined text-base">check_circle</span>
          <span className="font-body text-[13px]">Account created! Redirecting to verify your email...</span>
        </div>
      )}

      <form onSubmit={handleSubmit} className="flex flex-col gap-3">
        <div>
          <label className="type-mono-label text-[var(--c-text-3)] mb-1.5 block">Full Name</label>
          <input className="input-field" id="full-name" value={fullName} onChange={(e) => setFullName(e.target.value)} required type="text" placeholder="John Doe" />
        </div>
        <div>
          <label className="type-mono-label text-[var(--c-text-3)] mb-1.5 block">Email</label>
          <input className="input-field" id="reg-email" value={email} onChange={(e) => setEmail(e.target.value)} required type="email" placeholder="you@example.com" />
        </div>
        <div>
          <label className="type-mono-label text-[var(--c-text-3)] mb-1.5 block">Password</label>
          <input className="input-field" id="reg-password" value={password} onChange={(e) => setPassword(e.target.value)} required type="password" placeholder="••••••••" />
        </div>
        <div>
          <label className="type-mono-label text-[var(--c-text-3)] mb-1.5 block">Confirm Password</label>
          <input className="input-field" id="confirm-password" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} required type="password" placeholder="••••••••" />
        </div>

        <button disabled={loading} className="btn-primary w-full py-2.5 text-[14px] mt-1 btn-press disabled:opacity-50" type="submit">
          {loading && <span className="w-4 h-4 border-2 border-transparent border-t-current rounded-full animate-spin" />}
          {loading ? 'Creating account...' : 'Create account'}
        </button>
      </form>

      <p className="mt-8 text-center text-[var(--c-text-2)] font-body text-[13px]">
        Already have an account?{' '}
        <Link to="/login" className="text-primary font-medium hover:underline no-underline">Sign in</Link>
      </p>
    </div>
  );
}
