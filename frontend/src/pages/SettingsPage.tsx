import { useState, useEffect } from 'react';
import { useDocumentTitle } from '@/hooks/useDocumentTitle';
import { useTheme, type Theme } from '@/hooks/useTheme';
import { useAuth } from '@/store/AuthContext';
import { updateProfile } from '@/services/userService';
import { cn } from '@/utils/cn';

const THEME_OPTIONS: { value: Theme; label: string; icon: string }[] = [
  { value: 'light', label: 'Light', icon: 'light_mode' },
  { value: 'dark', label: 'Dark', icon: 'dark_mode' },
  { value: 'system', label: 'System', icon: 'contrast' },
];

export default function SettingsPage() {
  useDocumentTitle('Settings — NexusAI');
  const { theme, setTheme } = useTheme();
  const { user, refreshUser } = useAuth();

  const [fullName, setFullName] = useState('');
  const [username, setUsername] = useState('');
  const [bio, setBio] = useState('');
  const [college, setCollege] = useState('');
  const [degree, setDegree] = useState('');
  const [graduationYear, setGraduationYear] = useState('');
  const [country, setCountry] = useState('');
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (user) {
      setFullName(user.full_name ?? '');
      setUsername(user.username ?? '');
      setBio(user.bio ?? '');
      setCollege(user.college ?? '');
      setDegree(user.degree ?? '');
      setGraduationYear(user.graduation_year?.toString() ?? '');
      setCountry(user.country ?? '');
    }
  }, [user]);

  async function handleSaveProfile() {
    setSaving(true); setError(''); setSaved(false);
    try {
      const result = await updateProfile({
        full_name: fullName || undefined, username: username || undefined,
        bio: bio || undefined, college: college || undefined,
        degree: degree || undefined, graduation_year: graduationYear ? parseInt(graduationYear) : undefined,
        country: country || undefined,
      });
      if (result.success) { await refreshUser(); setSaved(true); setTimeout(() => setSaved(false), 3000); }
      else { setError(result.error?.message ?? 'Failed to save.'); }
    } catch { setError('Network error. Please try again.'); }
    finally { setSaving(false); }
  }

  return (
    <div className="flex flex-col min-h-screen">
      <div className="sticky top-0 z-10 bg-surface/90 backdrop-blur-md border-b border-outline-variant px-4 py-3">
        <h2 className="font-headline font-semibold text-[16px] text-on-surface tracking-tight">Settings</h2>
      </div>

      <div className="p-4 flex flex-col gap-4">
        {/* Theme */}
        <section className="card-intel p-4">
          <div className="flex items-center gap-2 mb-1">
            <span className="material-symbols-outlined text-base text-[var(--c-text-3)]">palette</span>
            <h3 className="type-mono-label text-[var(--c-text-3)]">Display</h3>
          </div>
          <p className="text-[var(--c-text-3)] text-[12px] font-body mb-4">Manage your display preferences.</p>

          <div className="grid grid-cols-3 gap-2">
            {THEME_OPTIONS.map((opt) => (
              <button
                key={opt.value}
                onClick={() => setTheme(opt.value)}
                className={cn(
                  'flex flex-col items-center gap-1.5 py-3 px-2 rounded border transition-all cursor-pointer bg-transparent font-body text-[12px]',
                  theme === opt.value
                    ? 'border-primary text-primary'
                    : 'border-[var(--c-border-subtle)] text-[var(--c-text-2)] hover:border-[var(--c-border)]'
                )}
              >
                <span className={cn('material-symbols-outlined text-xl', theme === opt.value && 'icon-fill')}>
                  {opt.icon}
                </span>
                <span className="font-medium">{opt.label}</span>
                {theme === opt.value && <span className="w-1.5 h-1.5 rounded-full bg-primary" />}
              </button>
            ))}
          </div>
        </section>

        {/* Account */}
        <section className="card-intel p-4">
          <div className="flex items-center gap-2 mb-1">
            <span className="material-symbols-outlined text-base text-[var(--c-text-3)]">person</span>
            <h3 className="type-mono-label text-[var(--c-text-3)]">Account</h3>
          </div>
          <p className="text-[var(--c-text-3)] text-[12px] font-body mb-4">Manage your profile information.</p>

          <div className="flex flex-col gap-3">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="type-mono-label text-[var(--c-text-3)] mb-1.5 block">Full Name</label>
                <input className="input-field text-[13px]" type="text" value={fullName} onChange={(e) => setFullName(e.target.value)} />
              </div>
              <div>
                <label className="type-mono-label text-[var(--c-text-3)] mb-1.5 block">Username</label>
                <input className="input-field text-[13px]" type="text" placeholder="@username" value={username} onChange={(e) => setUsername(e.target.value)} />
              </div>
            </div>
            <div>
              <label className="type-mono-label text-[var(--c-text-3)] mb-1.5 block">Email</label>
              <input className="input-field text-[13px] opacity-60" type="email" value={user?.email ?? ''} disabled />
            </div>
            <div>
              <label className="type-mono-label text-[var(--c-text-3)] mb-1.5 block">Bio</label>
              <textarea className="input-field text-[13px] resize-none h-20" value={bio} onChange={(e) => setBio(e.target.value)} maxLength={500} />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="type-mono-label text-[var(--c-text-3)] mb-1.5 block">College</label>
                <input className="input-field text-[13px]" type="text" value={college} onChange={(e) => setCollege(e.target.value)} />
              </div>
              <div>
                <label className="type-mono-label text-[var(--c-text-3)] mb-1.5 block">Degree</label>
                <input className="input-field text-[13px]" type="text" value={degree} onChange={(e) => setDegree(e.target.value)} />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="type-mono-label text-[var(--c-text-3)] mb-1.5 block">Graduation Year</label>
                <input className="input-field text-[13px]" type="number" min={1950} max={2040} value={graduationYear} onChange={(e) => setGraduationYear(e.target.value)} />
              </div>
              <div>
                <label className="type-mono-label text-[var(--c-text-3)] mb-1.5 block">Country</label>
                <input className="input-field text-[13px]" type="text" value={country} onChange={(e) => setCountry(e.target.value)} />
              </div>
            </div>

            {error && (
              <div className="flex items-center gap-2 text-[var(--c-danger)] p-3 bg-[var(--c-danger-dim)] rounded border border-[var(--c-danger)]/20">
                <span className="material-symbols-outlined text-base">error</span>
                <span className="font-body text-[13px]">{error}</span>
              </div>
            )}

            {saved && (
              <div className="flex items-center gap-2 text-[var(--c-tertiary)] p-3 bg-[var(--c-tertiary-dim)] rounded border border-[var(--c-tertiary)]/20">
                <span className="material-symbols-outlined text-base icon-fill">check_circle</span>
                <span className="font-body text-[13px]">Profile saved successfully.</span>
              </div>
            )}

            <button onClick={handleSaveProfile} disabled={saving}
              className="btn-primary self-start text-[12px] btn-press disabled:opacity-50">
              {saving && <span className="w-3.5 h-3.5 border-2 border-transparent border-t-current rounded-full animate-spin" />}
              {saving ? 'Saving...' : 'Save Profile'}
            </button>
          </div>
        </section>

        {/* Security */}
        <section className="card-intel p-4">
          <div className="flex items-center gap-2 mb-1">
            <span className="material-symbols-outlined text-base text-[var(--c-text-3)]">shield</span>
            <h3 className="type-mono-label text-[var(--c-text-3)]">Security</h3>
          </div>
          <p className="text-[var(--c-text-3)] text-[12px] font-body mb-4">Manage passwords and access.</p>

          <div className="flex flex-col gap-3">
            <div className="flex justify-between items-center py-2">
              <div>
                <p className="font-body font-medium text-[13px] text-on-surface">Password</p>
                <p className="font-body text-[12px] text-[var(--c-text-3)]">Change your account password</p>
              </div>
              <span className="badge badge-neutral">Coming soon</span>
            </div>
            <div className="flex justify-between items-center py-2 border-t border-outline-variant">
              <div>
                <p className="font-body font-medium text-[13px] text-on-surface">Two-Factor Auth</p>
                <p className="font-body text-[12px] text-[var(--c-text-3)]">Not yet available</p>
              </div>
              <span className="badge badge-neutral">Coming soon</span>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
