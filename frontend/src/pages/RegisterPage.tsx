import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useDocumentTitle } from '@/hooks/useDocumentTitle';
import { registerUser } from '@/services/authService';

export default function RegisterPage() {
  useDocumentTitle('Sign up — AI News Notifier');
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

    if (password !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }

    setLoading(true);
    try {
      const result = await registerUser(email, password, fullName);
      if (result.success) {
        setSuccess(true);
        setTimeout(() => navigate('/login'), 2000);
      } else {
        setError(result.error?.message ?? 'Registration failed.');
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

      <h1 className="text-3xl font-bold text-on-surface mb-2">Create your account</h1>
      <p className="text-on-surface-variant font-body mb-6">Join the AI intelligence network.</p>

      {/* Error */}
      {error && (
        <div className="flex items-center gap-2 text-error mb-4 p-3 bg-error-container rounded-lg">
          <span className="material-symbols-outlined text-lg">error</span>
          <span className="font-body text-sm">{error}</span>
        </div>
      )}

      {/* Success */}
      {success && (
        <div className="flex items-center gap-2 text-on-surface mb-4 p-3 bg-primary-container rounded-lg">
          <span className="material-symbols-outlined text-lg text-primary">check_circle</span>
          <span className="font-body text-sm">Account created! Redirecting to login...</span>
        </div>
      )}

      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <input
          className="input-field"
          id="full-name"
          value={fullName}
          onChange={(e) => setFullName(e.target.value)}
          required
          type="text"
          placeholder="Full name"
        />
        <input
          className="input-field"
          id="reg-email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
          type="email"
          placeholder="Email"
        />
        <input
          className="input-field"
          id="reg-password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          type="password"
          placeholder="Password"
        />
        <input
          className="input-field"
          id="confirm-password"
          value={confirmPassword}
          onChange={(e) => setConfirmPassword(e.target.value)}
          required
          type="password"
          placeholder="Confirm password"
        />

        <button
          disabled={loading}
          className="w-full bg-primary text-on-primary py-3 rounded-full font-bold text-[15px] font-body hover:opacity-90 transition-opacity border-none cursor-pointer disabled:opacity-50 flex items-center justify-center gap-2"
          type="submit"
        >
          {loading && <span className="w-4 h-4 border-2 border-transparent border-t-current rounded-full animate-spin" />}
          {loading ? 'Creating account...' : 'Sign up'}
        </button>
      </form>

      <p className="mt-8 text-center text-on-surface-variant font-body text-[15px]">
        Already have an account?{' '}
        <Link to="/login" className="text-primary font-bold hover:underline no-underline">
          Sign in
        </Link>
      </p>
    </div>
  );
}
