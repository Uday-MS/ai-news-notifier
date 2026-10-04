/**
 * VerifyEmailPage — OTP entry for email verification.
 * 6-digit code input, resend with countdown, error/success states.
 */

import { useState, useEffect, useRef } from 'react';
import { useNavigate, useSearchParams, Link } from 'react-router-dom';
import { useDocumentTitle } from '@/hooks/useDocumentTitle';
import { verifyEmailOTP, resendOTP } from '@/services/authService';
import { useAuth } from '@/store/AuthContext';
import { storeTokens } from '@/services/apiClient';

export default function VerifyEmailPage() {
  useDocumentTitle('Verify Email — NexusAI');
  const navigate = useNavigate();
  const { refreshUser } = useAuth();
  const [searchParams] = useSearchParams();
  const email = searchParams.get('email') ?? '';

  const [otp, setOtp] = useState(['', '', '', '', '', '']);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [resendCooldown, setResendCooldown] = useState(60);
  const [resendLoading, setResendLoading] = useState(false);
  const inputRefs = useRef<(HTMLInputElement | null)[]>([]);

  useEffect(() => {
    if (resendCooldown <= 0) return;
    const timer = setInterval(() => setResendCooldown((c) => c - 1), 1000);
    return () => clearInterval(timer);
  }, [resendCooldown]);

  function handleChange(index: number, value: string) {
    if (!/^\d*$/.test(value)) return;
    const newOtp = [...otp];
    newOtp[index] = value.slice(-1);
    setOtp(newOtp);
    if (value && index < 5) inputRefs.current[index + 1]?.focus();
  }

  function handleKeyDown(index: number, e: React.KeyboardEvent) {
    if (e.key === 'Backspace' && !otp[index] && index > 0) inputRefs.current[index - 1]?.focus();
  }

  function handlePaste(e: React.ClipboardEvent) {
    e.preventDefault();
    const pasted = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, 6);
    if (pasted.length === 6) { setOtp(pasted.split('')); inputRefs.current[5]?.focus(); }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const code = otp.join('');
    if (code.length !== 6) { setError('Please enter all 6 digits.'); return; }
    setError(''); setLoading(true);
    try {
      const result = await verifyEmailOTP(email, code);
      if (result.success && result.data) {
        storeTokens(result.data.access_token, result.data.refresh_token);
        setSuccess(true);
        await refreshUser();
        setTimeout(() => navigate('/'), 1500);
      } else {
        setError(result.error?.message ?? 'Verification failed.');
        setOtp(['', '', '', '', '', '']);
        inputRefs.current[0]?.focus();
      }
    } catch { setError('Network error. Please try again.'); }
    finally { setLoading(false); }
  }

  async function handleResend() {
    if (resendCooldown > 0 || resendLoading) return;
    setResendLoading(true); setError('');
    try {
      const result = await resendOTP(email);
      if (result.success) setResendCooldown(60);
      else setError(result.error?.message ?? 'Could not resend code.');
    } catch { setError('Network error.'); }
    finally { setResendLoading(false); }
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

      <h1 className="font-headline font-bold text-[28px] text-on-surface mb-2 tracking-tight text-center">Verify your email</h1>
      <p className="text-[var(--c-text-2)] text-[13px] font-body text-center mb-8">
        We sent a 6-digit code to <strong className="text-on-surface font-mono text-[12px]">{email || 'your email'}</strong>
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
          <span className="font-body text-[13px]">Email verified! Redirecting...</span>
        </div>
      )}

      <form onSubmit={handleSubmit} className="flex flex-col gap-5">
        <div className="flex gap-2.5 justify-center" onPaste={handlePaste}>
          {otp.map((digit, i) => (
            <input
              key={i}
              ref={(el) => { inputRefs.current[i] = el; }}
              className="w-11 h-12 text-center text-xl font-bold font-mono rounded border border-[var(--c-border-subtle)] bg-[var(--c-base)] text-on-surface focus:border-primary focus:outline-none transition-colors tabular-nums"
              type="text" inputMode="numeric" maxLength={1} value={digit}
              onChange={(e) => handleChange(i, e.target.value)}
              onKeyDown={(e) => handleKeyDown(i, e)}
              disabled={loading || success} autoFocus={i === 0}
            />
          ))}
        </div>

        <button disabled={loading || success || otp.join('').length !== 6}
          className="btn-primary w-full py-2.5 text-[14px] btn-press disabled:opacity-50" type="submit">
          {loading && <span className="w-4 h-4 border-2 border-transparent border-t-current rounded-full animate-spin" />}
          {loading ? 'Verifying...' : 'Verify Email'}
        </button>
      </form>

      <div className="mt-6 text-center">
        <p className="text-[var(--c-text-2)] font-body text-[12px]">
          Didn't receive the code?{' '}
          {resendCooldown > 0 ? (
            <span className="font-mono text-[var(--c-text-3)] tabular-nums">Resend in {resendCooldown}s</span>
          ) : (
            <button onClick={handleResend} disabled={resendLoading}
              className="text-primary font-medium hover:underline bg-transparent border-none cursor-pointer font-body text-[12px]">
              {resendLoading ? 'Sending...' : 'Resend code'}
            </button>
          )}
        </p>
      </div>

      <p className="mt-8 text-center text-[var(--c-text-2)] font-body text-[13px]">
        <Link to="/login" className="text-primary font-medium hover:underline no-underline">Back to sign in</Link>
      </p>
    </div>
  );
}
