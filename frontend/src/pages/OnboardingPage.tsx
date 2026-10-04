import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useDocumentTitle } from '@/hooks/useDocumentTitle';
import { useAuth } from '@/store/AuthContext';
import { updateProfile, updateInterests, updatePreferences } from '@/services/userService';
import { cn } from '@/utils/cn';

const INTEREST_OPTIONS = [
  'OpenAI', 'Anthropic', 'Google DeepMind', 'Meta AI', 'Microsoft AI',
  'NVIDIA', 'Hugging Face', 'AI Agents', 'LLMs', 'Robotics',
  'Research Papers', 'Computer Vision', 'Prompt Engineering',
];

const OPPORTUNITY_OPTIONS = [
  'Internships', 'Jobs', 'Fellowships', 'Student Ambassador Programs',
  'Research', 'Hackathons', 'Open Source',
];

const NOTIFICATION_OPTIONS = [
  { value: 'instant', label: 'Instant', desc: 'Get notified as things happen' },
  { value: 'daily', label: 'Daily Digest', desc: 'One email per day with highlights' },
  { value: 'weekly', label: 'Weekly Digest', desc: 'Weekly summary of top stories' },
];

const STEPS = ['Welcome', 'Profile', 'Interests', 'Preferences', 'Complete'];

export default function OnboardingPage() {
  useDocumentTitle('Onboarding — NexusAI');
  const navigate = useNavigate();
  const { user, refreshUser } = useAuth();

  const [step, setStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const [username, setUsername] = useState('');
  const [bio, setBio] = useState('');
  const [college, setCollege] = useState('');
  const [degree, setDegree] = useState('');
  const [graduationYear, setGraduationYear] = useState('');
  const [country, setCountry] = useState('');
  const [selectedInterests, setSelectedInterests] = useState<string[]>([]);
  const [selectedOpportunities, setSelectedOpportunities] = useState<string[]>([]);
  const [notificationPref, setNotificationPref] = useState('daily');

  function toggleInterest(interest: string) {
    setSelectedInterests((prev) => prev.includes(interest) ? prev.filter((i) => i !== interest) : [...prev, interest]);
  }

  function toggleOpportunity(opp: string) {
    setSelectedOpportunities((prev) => prev.includes(opp) ? prev.filter((o) => o !== opp) : [...prev, opp]);
  }

  async function handleNext() {
    setError(''); setLoading(true);
    try {
      if (step === 1) {
        await updateProfile({ username: username || undefined, bio: bio || undefined, college: college || undefined, degree: degree || undefined, graduation_year: graduationYear ? parseInt(graduationYear) : undefined, country: country || undefined });
      } else if (step === 2) {
        await updateInterests(selectedInterests);
      } else if (step === 3) {
        await updatePreferences(selectedOpportunities);
        await updateProfile({ notification_preference: notificationPref });
      }
      if (step === 3) {
        setStep(4);
        await updateProfile({ onboarding_completed: true });
        await refreshUser();
      } else { setStep((s) => s + 1); }
    } catch { setError('Something went wrong. Please try again.'); }
    finally { setLoading(false); }
  }

  function handleBack() { if (step > 0) setStep((s) => s - 1); }

  function renderWelcome() {
    return (
      <div className="text-center py-8 page-transition">
        <div className="w-16 h-16 rounded bg-primary/10 flex items-center justify-center mx-auto mb-6">
          <span className="material-symbols-outlined text-primary text-4xl icon-fill">hub</span>
        </div>
        <h1 className="font-headline font-bold text-[28px] text-on-surface mb-3 tracking-tight">
          Welcome, {user?.full_name?.split(' ')[0] ?? 'there'}!
        </h1>
        <p className="text-[var(--c-text-2)] font-body text-[15px] mb-2 max-w-md mx-auto">
          Let's personalize your AI intelligence feed in a few quick steps.
        </p>
        <p className="font-mono text-[11px] text-[var(--c-text-3)] uppercase tracking-wider">~1 minute setup</p>
      </div>
    );
  }

  function renderProfile() {
    return (
      <div className="page-transition">
        <h2 className="font-headline font-semibold text-[20px] text-on-surface mb-1.5 tracking-tight">Your Profile</h2>
        <p className="text-[var(--c-text-2)] font-body text-[13px] mb-5">Tell us about yourself. All fields are optional.</p>
        <div className="flex flex-col gap-3">
          <div>
            <label className="type-mono-label text-[var(--c-text-3)] mb-1.5 block">Username</label>
            <input className="input-field text-[13px]" placeholder="@yourhandle" value={username} onChange={(e) => setUsername(e.target.value)} />
          </div>
          <div>
            <label className="type-mono-label text-[var(--c-text-3)] mb-1.5 block">Bio</label>
            <textarea className="input-field text-[13px] resize-none h-20" placeholder="A short bio about you..." value={bio} onChange={(e) => setBio(e.target.value)} maxLength={500} />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="type-mono-label text-[var(--c-text-3)] mb-1.5 block">College</label>
              <input className="input-field text-[13px]" placeholder="University" value={college} onChange={(e) => setCollege(e.target.value)} />
            </div>
            <div>
              <label className="type-mono-label text-[var(--c-text-3)] mb-1.5 block">Degree</label>
              <input className="input-field text-[13px]" placeholder="e.g. B.Tech CS" value={degree} onChange={(e) => setDegree(e.target.value)} />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="type-mono-label text-[var(--c-text-3)] mb-1.5 block">Grad Year</label>
              <input className="input-field text-[13px]" type="number" placeholder="2026" min={1950} max={2040} value={graduationYear} onChange={(e) => setGraduationYear(e.target.value)} />
            </div>
            <div>
              <label className="type-mono-label text-[var(--c-text-3)] mb-1.5 block">Country</label>
              <input className="input-field text-[13px]" placeholder="e.g. India" value={country} onChange={(e) => setCountry(e.target.value)} />
            </div>
          </div>
        </div>
      </div>
    );
  }

  function renderInterests() {
    return (
      <div className="page-transition">
        <h2 className="font-headline font-semibold text-[20px] text-on-surface mb-1.5 tracking-tight">What interests you?</h2>
        <p className="text-[var(--c-text-2)] font-body text-[13px] mb-5">Select topics to personalize your feed. Choose at least 3.</p>
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
          {INTEREST_OPTIONS.map((interest) => {
            const selected = selectedInterests.includes(interest);
            return (
              <button key={interest} type="button" onClick={() => toggleInterest(interest)}
                className={cn(
                  'px-3 py-2.5 rounded border font-body text-[12px] text-left transition-all cursor-pointer',
                  selected ? 'border-primary text-primary bg-[var(--c-accent-dim)]' : 'border-[var(--c-border-subtle)] text-[var(--c-text-2)] bg-transparent hover:border-[var(--c-border)]'
                )}>
                <span className="flex items-center gap-1.5">
                  {selected && <span className="material-symbols-outlined text-xs icon-fill">check_circle</span>}
                  {interest}
                </span>
              </button>
            );
          })}
        </div>
        <p className="font-mono text-[10px] text-[var(--c-text-3)] mt-3 uppercase tracking-wider">{selectedInterests.length} selected</p>
      </div>
    );
  }

  function renderPreferences() {
    return (
      <div className="page-transition">
        <h2 className="font-headline font-semibold text-[20px] text-on-surface mb-1.5 tracking-tight">Opportunity Preferences</h2>
        <p className="text-[var(--c-text-2)] font-body text-[13px] mb-5">What types of opportunities interest you?</p>
        <div className="flex flex-wrap gap-2 mb-6">
          {OPPORTUNITY_OPTIONS.map((opp) => {
            const selected = selectedOpportunities.includes(opp);
            return (
              <button key={opp} type="button" onClick={() => toggleOpportunity(opp)}
                className={cn(
                  'px-3 py-1.5 rounded border font-body text-[12px] transition-all cursor-pointer',
                  selected ? 'border-primary text-primary bg-[var(--c-accent-dim)]' : 'border-[var(--c-border-subtle)] text-[var(--c-text-2)] bg-transparent hover:border-[var(--c-border)]'
                )}>
                {selected && <span className="mr-1">✓</span>}
                {opp}
              </button>
            );
          })}
        </div>

        <h3 className="type-mono-label text-[var(--c-text-3)] mb-3">Notification Frequency</h3>
        <div className="flex flex-col gap-2">
          {NOTIFICATION_OPTIONS.map((opt) => (
            <label key={opt.value}
              className={cn(
                'flex items-center gap-3 p-3 rounded border cursor-pointer transition-all',
                notificationPref === opt.value ? 'border-primary bg-[var(--c-accent-dim)]' : 'border-[var(--c-border-subtle)] hover:border-[var(--c-border)]'
              )}>
              <input type="radio" name="notification" value={opt.value} checked={notificationPref === opt.value}
                onChange={() => setNotificationPref(opt.value)} className="w-3.5 h-3.5 accent-[var(--c-accent)]" />
              <div>
                <span className="font-body font-medium text-[13px] text-on-surface">{opt.label}</span>
                <span className="font-body text-[11px] text-[var(--c-text-3)] block">{opt.desc}</span>
              </div>
            </label>
          ))}
        </div>
      </div>
    );
  }

  function renderComplete() {
    return (
      <div className="text-center py-8 page-transition">
        <div className="w-16 h-16 rounded bg-[var(--c-tertiary-dim)] flex items-center justify-center mx-auto mb-6">
          <span className="material-symbols-outlined text-[var(--c-tertiary)] text-4xl icon-fill">rocket_launch</span>
        </div>
        <h2 className="font-headline font-bold text-[28px] text-on-surface mb-3 tracking-tight">You're all set!</h2>
        <p className="text-[var(--c-text-2)] font-body text-[15px] mb-8 max-w-md mx-auto">
          Your intelligence feed is personalized. Let's explore what's happening in AI.
        </p>
        <button onClick={() => navigate('/')} className="btn-primary py-2.5 px-8 text-[14px] btn-press">
          Launch Feed →
        </button>
      </div>
    );
  }

  const stepRenderers = [renderWelcome, renderProfile, renderInterests, renderPreferences, renderComplete];

  return (
    <div className="min-h-screen flex items-center justify-center bg-background text-on-surface p-4">
      <div className="w-full max-w-[520px]">
        {/* Progress */}
        <div className="flex items-center gap-1.5 mb-8">
          {STEPS.map((label, i) => (
            <div key={label} className="flex-1 flex flex-col items-center gap-1">
              <div className={cn('h-[2px] w-full rounded-full transition-colors', i <= step ? 'bg-primary' : 'bg-[var(--c-border-subtle)]')} />
              <span className={cn('font-mono text-[9px] uppercase tracking-wider hidden sm:block', i <= step ? 'text-primary' : 'text-[var(--c-text-4)]')}>
                {label}
              </span>
            </div>
          ))}
        </div>

        {stepRenderers[step]()}

        {error && (
          <div className="flex items-center gap-2 text-[var(--c-danger)] mt-4 p-3 bg-[var(--c-danger-dim)] rounded border border-[var(--c-danger)]/20">
            <span className="material-symbols-outlined text-base">error</span>
            <span className="font-body text-[13px]">{error}</span>
          </div>
        )}

        {step < 4 && (
          <div className="flex justify-between mt-8">
            {step > 0 ? (
              <button onClick={handleBack} disabled={loading} className="btn-secondary text-[12px] btn-press disabled:opacity-50">Back</button>
            ) : <div />}
            <button onClick={handleNext} disabled={loading} className="btn-primary text-[12px] btn-press disabled:opacity-50">
              {loading && <span className="w-3.5 h-3.5 border-2 border-transparent border-t-current rounded-full animate-spin" />}
              {step === 0 ? "Let's Go" : step === 3 ? 'Finish' : 'Continue'}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
