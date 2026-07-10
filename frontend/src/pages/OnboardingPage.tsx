import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useDocumentTitle } from '@/hooks/useDocumentTitle';
import { useAuth } from '@/store/AuthContext';
import { updateProfile, updateInterests, updatePreferences } from '@/services/userService';
import { cn } from '@/utils/cn';

// ── Data ────────────────────────────────────────────────────────────────

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

// ── Component ───────────────────────────────────────────────────────────

export default function OnboardingPage() {
  useDocumentTitle('Onboarding — AI News Notifier');
  const navigate = useNavigate();
  const { user, refreshUser } = useAuth();

  const [step, setStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Profile state
  const [username, setUsername] = useState('');
  const [bio, setBio] = useState('');
  const [college, setCollege] = useState('');
  const [degree, setDegree] = useState('');
  const [graduationYear, setGraduationYear] = useState('');
  const [country, setCountry] = useState('');

  // Interests state
  const [selectedInterests, setSelectedInterests] = useState<string[]>([]);

  // Preferences state
  const [selectedOpportunities, setSelectedOpportunities] = useState<string[]>([]);
  const [notificationPref, setNotificationPref] = useState('daily');

  function toggleInterest(interest: string) {
    setSelectedInterests((prev) =>
      prev.includes(interest) ? prev.filter((i) => i !== interest) : [...prev, interest]
    );
  }

  function toggleOpportunity(opp: string) {
    setSelectedOpportunities((prev) =>
      prev.includes(opp) ? prev.filter((o) => o !== opp) : [...prev, opp]
    );
  }

  async function handleNext() {
    setError('');
    setLoading(true);
    try {
      if (step === 1) {
        // Save profile
        await updateProfile({
          username: username || undefined,
          bio: bio || undefined,
          college: college || undefined,
          degree: degree || undefined,
          graduation_year: graduationYear ? parseInt(graduationYear) : undefined,
          country: country || undefined,
        });
      } else if (step === 2) {
        // Save interests
        await updateInterests(selectedInterests);
      } else if (step === 3) {
        // Save preferences + notification pref
        await updatePreferences(selectedOpportunities);
        await updateProfile({ notification_preference: notificationPref });
      }

      if (step === 3) {
        // Move to complete step, then mark onboarding done
        setStep(4);
        await updateProfile({ onboarding_completed: true });
        await refreshUser();
      } else {
        setStep((s) => s + 1);
      }
    } catch {
      setError('Something went wrong. Please try again.');
    } finally {
      setLoading(false);
    }
  }

  function handleBack() {
    if (step > 0) setStep((s) => s - 1);
  }

  // ── Step Rendering ────────────────────────────────────────────────────

  function renderWelcome() {
    return (
      <div className="text-center py-8 page-transition">
        <span className="material-symbols-outlined text-primary text-7xl mb-6 block icon-fill">hub</span>
        <h1 className="text-3xl font-headline text-on-surface mb-3">
          Welcome, {user?.full_name?.split(' ')[0] ?? 'there'}!
        </h1>
        <p className="text-on-surface-variant font-body text-lg mb-2 max-w-md mx-auto">
          Let's personalize your AI intelligence feed in a few quick steps.
        </p>
        <p className="text-on-surface-variant font-body text-sm">This takes about 1 minute.</p>
      </div>
    );
  }

  function renderProfile() {
    return (
      <div className="page-transition">
        <h2 className="text-2xl font-headline text-on-surface mb-2">Your Profile</h2>
        <p className="text-on-surface-variant font-body mb-6">Tell us about yourself. All fields are optional.</p>
        <div className="flex flex-col gap-4">
          <div>
            <label className="font-body text-sm font-medium text-on-surface-variant block mb-1.5">Username</label>
            <input className="input-field" placeholder="@yourhandle" value={username} onChange={(e) => setUsername(e.target.value)} />
          </div>
          <div>
            <label className="font-body text-sm font-medium text-on-surface-variant block mb-1.5">Bio</label>
            <textarea className="input-field resize-none h-20" placeholder="A short bio about you..." value={bio} onChange={(e) => setBio(e.target.value)} maxLength={500} />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="font-body text-sm font-medium text-on-surface-variant block mb-1.5">College</label>
              <input className="input-field" placeholder="University name" value={college} onChange={(e) => setCollege(e.target.value)} />
            </div>
            <div>
              <label className="font-body text-sm font-medium text-on-surface-variant block mb-1.5">Degree</label>
              <input className="input-field" placeholder="e.g. B.Tech CS" value={degree} onChange={(e) => setDegree(e.target.value)} />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="font-body text-sm font-medium text-on-surface-variant block mb-1.5">Graduation Year</label>
              <input className="input-field" type="number" placeholder="2026" min={1950} max={2040} value={graduationYear} onChange={(e) => setGraduationYear(e.target.value)} />
            </div>
            <div>
              <label className="font-body text-sm font-medium text-on-surface-variant block mb-1.5">Country</label>
              <input className="input-field" placeholder="e.g. India" value={country} onChange={(e) => setCountry(e.target.value)} />
            </div>
          </div>
        </div>
      </div>
    );
  }

  function renderInterests() {
    return (
      <div className="page-transition">
        <h2 className="text-2xl font-headline text-on-surface mb-2">What are you interested in?</h2>
        <p className="text-on-surface-variant font-body mb-6">
          Select topics to personalize your feed. Choose at least 3.
        </p>
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
          {INTEREST_OPTIONS.map((interest) => {
            const selected = selectedInterests.includes(interest);
            return (
              <button
                key={interest}
                type="button"
                onClick={() => toggleInterest(interest)}
                className={cn(
                  'px-4 py-3 rounded-xl border-2 font-body text-sm text-left transition-all cursor-pointer bg-surface',
                  selected
                    ? 'border-primary text-primary bg-primary-container'
                    : 'border-outline text-on-surface hover:border-on-surface-variant'
                )}
              >
                <span className="flex items-center gap-2">
                  {selected && <span className="material-symbols-outlined text-base icon-fill">check_circle</span>}
                  {interest}
                </span>
              </button>
            );
          })}
        </div>
        <p className="text-on-surface-variant text-sm font-body mt-4">
          {selectedInterests.length} selected
        </p>
      </div>
    );
  }

  function renderPreferences() {
    return (
      <div className="page-transition">
        <h2 className="text-2xl font-headline text-on-surface mb-2">Opportunity Preferences</h2>
        <p className="text-on-surface-variant font-body mb-6">What types of opportunities interest you?</p>
        <div className="flex flex-wrap gap-3 mb-8">
          {OPPORTUNITY_OPTIONS.map((opp) => {
            const selected = selectedOpportunities.includes(opp);
            return (
              <button
                key={opp}
                type="button"
                onClick={() => toggleOpportunity(opp)}
                className={cn(
                  'px-4 py-2.5 rounded-full border-2 font-body text-sm transition-all cursor-pointer bg-surface',
                  selected
                    ? 'border-primary text-primary bg-primary-container'
                    : 'border-outline text-on-surface hover:border-on-surface-variant'
                )}
              >
                {selected && <span className="mr-1.5">✓</span>}
                {opp}
              </button>
            );
          })}
        </div>

        <h3 className="text-lg font-headline text-on-surface mb-2">Notification Frequency</h3>
        <p className="text-on-surface-variant font-body text-sm mb-4">How often should we notify you?</p>
        <div className="flex flex-col gap-3">
          {NOTIFICATION_OPTIONS.map((opt) => (
            <label
              key={opt.value}
              className={cn(
                'flex items-center gap-3 p-4 rounded-xl border-2 cursor-pointer transition-all bg-surface',
                notificationPref === opt.value
                  ? 'border-primary'
                  : 'border-outline hover:border-on-surface-variant'
              )}
            >
              <input
                type="radio"
                name="notification"
                value={opt.value}
                checked={notificationPref === opt.value}
                onChange={() => setNotificationPref(opt.value)}
                className="w-4 h-4 accent-[var(--c-primary)]"
              />
              <div>
                <span className="font-body font-bold text-sm text-on-surface">{opt.label}</span>
                <span className="font-body text-sm text-on-surface-variant block">{opt.desc}</span>
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
        <span className="material-symbols-outlined text-primary text-7xl mb-6 block icon-fill">
          rocket_launch
        </span>
        <h2 className="text-3xl font-headline text-on-surface mb-3">You're all set!</h2>
        <p className="text-on-surface-variant font-body text-lg mb-8 max-w-md mx-auto">
          Your intelligence feed is personalized. Let's explore what's happening in AI.
        </p>
        <button
          onClick={() => navigate('/')}
          className="bg-primary text-on-primary px-8 py-3 rounded-full font-bold text-[15px] font-body hover:opacity-90 transition-opacity border-none cursor-pointer"
        >
          Launch Feed →
        </button>
      </div>
    );
  }

  const stepRenderers = [renderWelcome, renderProfile, renderInterests, renderPreferences, renderComplete];

  // ── Main Render ───────────────────────────────────────────────────────

  return (
    <div className="min-h-screen flex items-center justify-center bg-background text-on-surface p-4">
      <div className="w-full max-w-[540px]">
        {/* Progress Bar */}
        <div className="flex items-center gap-2 mb-8">
          {STEPS.map((label, i) => (
            <div key={label} className="flex-1 flex flex-col items-center gap-1">
              <div
                className={cn(
                  'h-1 w-full rounded-full transition-colors',
                  i <= step ? 'bg-primary' : 'bg-outline'
                )}
              />
              <span className={cn(
                'text-[10px] font-body hidden sm:block',
                i <= step ? 'text-primary' : 'text-on-surface-variant'
              )}>
                {label}
              </span>
            </div>
          ))}
        </div>

        {/* Step Content */}
        {stepRenderers[step]()}

        {/* Error */}
        {error && (
          <div className="flex items-center gap-2 text-error mt-4 p-3 bg-error-container rounded-lg">
            <span className="material-symbols-outlined text-lg">error</span>
            <span className="font-body text-sm">{error}</span>
          </div>
        )}

        {/* Navigation */}
        {step < 4 && (
          <div className="flex justify-between mt-8">
            {step > 0 ? (
              <button
                onClick={handleBack}
                disabled={loading}
                className="px-6 py-2.5 rounded-full border border-outline text-on-surface font-body font-bold text-sm hover:bg-surface-container transition-colors bg-transparent cursor-pointer disabled:opacity-50"
              >
                Back
              </button>
            ) : (
              <div />
            )}
            <button
              onClick={handleNext}
              disabled={loading}
              className="bg-primary text-on-primary px-6 py-2.5 rounded-full font-bold text-sm font-body hover:opacity-90 transition-opacity border-none cursor-pointer disabled:opacity-50 flex items-center gap-2"
            >
              {loading && <span className="w-4 h-4 border-2 border-transparent border-t-current rounded-full animate-spin" />}
              {step === 0 ? "Let's Go" : step === 3 ? 'Finish' : 'Continue'}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
