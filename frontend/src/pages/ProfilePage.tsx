import { useNavigate } from 'react-router-dom';
import { useDocumentTitle } from '@/hooks/useDocumentTitle';
import { useAuth } from '@/store/AuthContext';

export default function ProfilePage() {
  useDocumentTitle('Profile — AI News Notifier');
  const { user } = useAuth();
  const navigate = useNavigate();

  const joinDate = user?.created_at
    ? new Date(user.created_at).toLocaleDateString('en-US', { month: 'long', year: 'numeric' })
    : 'Member';

  return (
    <div className="flex flex-col min-h-screen">
      <div className="sticky top-0 z-10 bg-surface/95 backdrop-blur-md border-b border-outline px-4 py-2.5">
        <h2 className="text-xl font-bold text-on-surface">{user?.full_name || 'Profile'}</h2>
      </div>

      {/* Cover */}
      <div className="h-[200px] bg-gradient-to-br from-[var(--c-elevated)] to-[var(--c-overlay)]" />

      {/* Avatar + Edit */}
      <div className="px-4 -mt-[66px] flex justify-between items-end mb-3">
        <div className="w-[132px] h-[132px] rounded-full bg-surface border-4 border-surface flex items-center justify-center">
          <div className="w-[124px] h-[124px] rounded-full bg-[var(--c-elevated)] flex items-center justify-center">
            <span className="text-5xl font-bold text-on-surface-variant">{user?.full_name?.charAt(0)?.toUpperCase() || 'U'}</span>
          </div>
        </div>
        <button onClick={() => navigate('/settings')}
          className="px-4 py-1.5 rounded-full border border-[var(--c-border-strong)] text-on-surface font-semibold text-[15px] hover:bg-[var(--c-elevated)] transition-colors bg-transparent cursor-pointer">
          Edit profile
        </button>
      </div>

      {/* Info */}
      <div className="px-4 pb-3 border-b border-outline">
        <h1 className="text-xl font-bold text-on-surface leading-tight">{user?.full_name || 'User'}</h1>
        {user?.username && <p className="text-[15px] text-on-surface-variant">@{user.username}</p>}

        {user?.bio ? (
          <p className="text-[15px] text-on-surface leading-[1.4] mt-3">{user.bio}</p>
        ) : (
          <p className="text-[15px] text-on-surface-variant mt-3">No bio yet. <button onClick={() => navigate('/settings')} className="text-primary hover:underline bg-transparent border-none cursor-pointer text-[15px] p-0">Add one</button></p>
        )}

        <div className="flex flex-wrap gap-x-4 gap-y-1 mt-3 text-[15px] text-on-surface-variant">
          {user?.college && <span className="flex items-center gap-1"><span className="material-symbols-outlined text-base">business</span>{user.college}</span>}
          {user?.country && <span className="flex items-center gap-1"><span className="material-symbols-outlined text-base">location_on</span>{user.country}</span>}
          {user?.degree && <span className="flex items-center gap-1"><span className="material-symbols-outlined text-base">school</span>{user.degree}</span>}
          <span className="flex items-center gap-1"><span className="material-symbols-outlined text-base">calendar_month</span>Joined {joinDate}</span>
        </div>


      </div>

      <div className="px-4 py-4">
        <h3 className="text-[15px] font-semibold text-on-surface mb-3">Activity</h3>
        {[
          { icon: 'menu_book', text: 'Reading AI research papers', detail: 'Personalized feed active' },
          { icon: 'bookmark', text: 'Saving articles for later', detail: 'Visit Saved to review' },
          { icon: 'notifications', text: 'Receiving AI news alerts', detail: 'Based on your interests' },
        ].map((a) => (
          <div key={a.icon} className="flex items-start gap-3 py-2">
            <span className="material-symbols-outlined text-on-surface-variant text-xl mt-0.5">{a.icon}</span>
            <div>
              <p className="text-[15px] text-on-surface">{a.text}</p>
              <p className="text-[13px] text-on-surface-variant">{a.detail}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
