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
  useDocumentTitle('Settings — AI News Notifier');
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

  // Populate from current user
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
    setSaving(true);
    setError('');
    setSaved(false);
    try {
      const result = await updateProfile({
        full_name: fullName || undefined,
        username: username || undefined,
        bio: bio || undefined,
        college: college || undefined,
        degree: degree || undefined,
        graduation_year: graduationYear ? parseInt(graduationYear) : undefined,
        country: country || undefined,
      });
      if (result.success) {
        await refreshUser();
        setSaved(true);
        setTimeout(() => setSaved(false), 3000);
      } else {
        setError(result.error?.message ?? 'Failed to save.');
      }
    } catch {
      setError('Network error. Please try again.');
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="flex flex-col min-h-screen">
      {/* Sticky Header */}
      <div className="sticky top-0 z-10 bg-surface/95 backdrop-blur-md border-b border-outline px-4 py-3">
        <h2 className="text-xl font-bold font-body text-on-surface">Settings</h2>
      </div>

      <div className="p-4 flex flex-col gap-6">
        {/* Theme Section */}
        <section className="bg-surface-container-low rounded-2xl p-5">
          <h3 className="font-body font-bold text-on-surface text-lg mb-1 flex items-center gap-2">
            <span className="material-symbols-outlined text-xl">palette</span>
            Display
          </h3>
          <p className="text-on-surface-variant text-sm font-body mb-4">Manage your display preferences.</p>

          <div className="mb-4">
            <label className="font-body text-sm font-medium text-on-surface-variant block mb-3">Theme</label>
            <div className="grid grid-cols-3 gap-3">
              {THEME_OPTIONS.map((opt) => (
                <button
                  key={opt.value}
                  onClick={() => setTheme(opt.value)}
                  className={cn(
                    'flex flex-col items-center gap-2 py-4 px-3 rounded-xl border-2 transition-all cursor-pointer bg-surface font-body',
                    theme === opt.value
                      ? 'border-primary text-primary'
                      : 'border-outline text-on-surface-variant hover:border-on-surface-variant'
                  )}
                >
                  <span className={cn('material-symbols-outlined text-2xl', theme === opt.value && 'icon-fill')}>
                    {opt.icon}
                  </span>
                  <span className="text-sm font-medium">{opt.label}</span>
                  {theme === opt.value && (
                    <span className="w-2 h-2 rounded-full bg-primary" />
                  )}
                </button>
              ))}
            </div>
          </div>
        </section>

        {/* Account Section — wired to real user data */}
        <section className="bg-surface-container-low rounded-2xl p-5">
          <h3 className="font-body font-bold text-on-surface text-lg mb-1 flex items-center gap-2">
            <span className="material-symbols-outlined text-xl">person</span>
            Account
          </h3>
          <p className="text-on-surface-variant text-sm font-body mb-4">Manage your profile information.</p>

          <div className="flex flex-col gap-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="font-body text-sm font-medium text-on-surface-variant block mb-1.5">Full Name</label>
                <input className="input-field" type="text" value={fullName} onChange={(e) => setFullName(e.target.value)} />
              </div>
              <div>
                <label className="font-body text-sm font-medium text-on-surface-variant block mb-1.5">Username</label>
                <input className="input-field" type="text" placeholder="@username" value={username} onChange={(e) => setUsername(e.target.value)} />
              </div>
            </div>
            <div>
              <label className="font-body text-sm font-medium text-on-surface-variant block mb-1.5">Email</label>
              <input className="input-field" type="email" value={user?.email ?? ''} disabled />
            </div>
            <div>
              <label className="font-body text-sm font-medium text-on-surface-variant block mb-1.5">Bio</label>
              <textarea className="input-field resize-none h-20" value={bio} onChange={(e) => setBio(e.target.value)} maxLength={500} />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="font-body text-sm font-medium text-on-surface-variant block mb-1.5">College</label>
                <input className="input-field" type="text" value={college} onChange={(e) => setCollege(e.target.value)} />
              </div>
              <div>
                <label className="font-body text-sm font-medium text-on-surface-variant block mb-1.5">Degree</label>
                <input className="input-field" type="text" value={degree} onChange={(e) => setDegree(e.target.value)} />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="font-body text-sm font-medium text-on-surface-variant block mb-1.5">Graduation Year</label>
                <input className="input-field" type="number" min={1950} max={2040} value={graduationYear} onChange={(e) => setGraduationYear(e.target.value)} />
              </div>
              <div>
                <label className="font-body text-sm font-medium text-on-surface-variant block mb-1.5">Country</label>
                <input className="input-field" type="text" value={country} onChange={(e) => setCountry(e.target.value)} />
              </div>
            </div>

            {error && (
              <div className="flex items-center gap-2 text-error p-3 bg-error-container rounded-lg">
                <span className="material-symbols-outlined text-lg">error</span>
                <span className="font-body text-sm">{error}</span>
              </div>
            )}

            {saved && (
              <div className="flex items-center gap-2 p-3 bg-primary-container rounded-lg">
                <span className="material-symbols-outlined text-lg text-primary icon-fill">check_circle</span>
                <span className="font-body text-sm text-on-surface">Profile saved successfully.</span>
              </div>
            )}

            <button
              onClick={handleSaveProfile}
              disabled={saving}
              className="self-start bg-primary text-on-primary px-6 py-2.5 rounded-full font-bold text-sm font-body hover:opacity-90 transition-opacity border-none cursor-pointer disabled:opacity-50 flex items-center gap-2"
            >
              {saving && <span className="w-4 h-4 border-2 border-transparent border-t-current rounded-full animate-spin" />}
              {saving ? 'Saving...' : 'Save Profile'}
            </button>
          </div>
        </section>

        {/* Security Section */}
        <section className="bg-surface-container-low rounded-2xl p-5">
          <h3 className="font-body font-bold text-on-surface text-lg mb-1 flex items-center gap-2">
            <span className="material-symbols-outlined text-xl">shield</span>
            Security
          </h3>
          <p className="text-on-surface-variant text-sm font-body mb-4">Manage passwords and access.</p>

          <div className="flex flex-col gap-3">
            <div className="flex justify-between items-center py-2">
              <div>
                <p className="font-body font-medium text-sm text-on-surface">Password</p>
                <p className="font-body text-sm text-on-surface-variant">Change your account password</p>
              </div>
              <span className="px-4 py-2 rounded-full border border-outline text-on-surface-variant font-body text-sm opacity-50">
                Coming soon
              </span>
            </div>
            <div className="flex justify-between items-center py-2 border-t border-outline">
              <div>
                <p className="font-body font-medium text-sm text-on-surface">Two-Factor Authentication</p>
                <p className="font-body text-sm text-on-surface-variant">Not yet available</p>
              </div>
              <span className="px-4 py-2 rounded-full border border-outline text-on-surface-variant font-body text-sm opacity-50">
                Coming soon
              </span>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
