import { useNavigate } from 'react-router-dom';
import { useDocumentTitle } from '@/hooks/useDocumentTitle';
import { useAuth } from '@/store/AuthContext';

export default function ProfilePage() {
  useDocumentTitle('Profile — NexusAI');
  const { user } = useAuth();
  const navigate = useNavigate();

  const joinDate = user?.created_at
    ? new Date(user.created_at).toLocaleDateString('en-US', { month: 'long', year: 'numeric' })
    : 'Member';

  return (
    <div className="flex flex-col min-h-screen">
      <div className="sticky top-0 z-10 bg-surface/90 backdrop-blur-md border-b border-outline-variant px-4 py-3">
        <h2 className="font-headline font-semibold text-[16px] text-on-surface tracking-tight">{user?.full_name || 'Profile'}</h2>
      </div>

      {/* Cover gradient */}
      <div className="h-[140px] bg-gradient-to-br from-primary/10 via-secondary/10 to-[var(--c-elevated)]" />

      {/* Avatar + Edit */}
      <div className="px-4 -mt-[50px] flex justify-between items-end mb-3">
        <div className="w-[100px] h-[100px] rounded bg-surface border-4 border-surface flex items-center justify-center">
          <div className="w-[92px] h-[92px] rounded bg-[var(--c-elevated)] flex items-center justify-center">
            <span className="text-3xl font-bold text-[var(--c-text-2)] font-headline">{user?.full_name?.charAt(0)?.toUpperCase() || 'U'}</span>
          </div>
        </div>
        <button onClick={() => navigate('/settings')}
          className="btn-secondary text-[12px]">
          Edit profile
        </button>
      </div>

      {/* Info */}
      <div className="px-4 pb-4 border-b border-outline-variant">
        <h1 className="font-headline font-bold text-[20px] text-on-surface leading-tight tracking-tight">{user?.full_name || 'User'}</h1>
        {user?.username && <p className="font-mono text-[12px] text-[var(--c-text-3)] mt-0.5">@{user.username}</p>}

        {user?.bio ? (
          <p className="text-[13px] text-[var(--c-text-2)] leading-[1.5] mt-3 font-body">{user.bio}</p>
        ) : (
          <p className="text-[13px] text-[var(--c-text-3)] mt-3 font-body">
            No bio yet.{' '}
            <button onClick={() => navigate('/settings')} className="text-primary hover:underline bg-transparent border-none cursor-pointer text-[13px] p-0 font-body">Add one</button>
          </p>
        )}

        <div className="flex flex-wrap gap-x-4 gap-y-1 mt-3 text-[12px] text-[var(--c-text-3)]">
          {user?.college && <span className="flex items-center gap-1"><span className="material-symbols-outlined text-sm">business</span>{user.college}</span>}
          {user?.country && <span className="flex items-center gap-1"><span className="material-symbols-outlined text-sm">location_on</span>{user.country}</span>}
          {user?.degree && <span className="flex items-center gap-1"><span className="material-symbols-outlined text-sm">school</span>{user.degree}</span>}
          <span className="flex items-center gap-1 font-mono"><span className="material-symbols-outlined text-sm">calendar_month</span>Joined {joinDate}</span>
        </div>
      </div>

      {/* Activity */}
      <div className="px-4 py-4">
        <h3 className="type-mono-label text-[var(--c-text-3)] mb-3">Activity</h3>
        {[
          { icon: 'menu_book', text: 'Reading AI research', detail: 'Personalized feed active' },
          { icon: 'bookmark', text: 'Saving intelligence', detail: 'Visit Saved to review' },
          { icon: 'notifications', text: 'Receiving alerts', detail: 'Based on your interests' },
        ].map((a) => (
          <div key={a.icon} className="flex items-start gap-2.5 py-2">
            <span className="material-symbols-outlined text-[var(--c-text-3)] text-lg mt-0.5">{a.icon}</span>
            <div>
              <p className="text-[13px] text-on-surface font-body">{a.text}</p>
              <p className="text-[11px] text-[var(--c-text-3)] font-body">{a.detail}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
