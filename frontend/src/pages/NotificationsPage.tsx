import { useState, useEffect, useCallback } from 'react';
import { useDocumentTitle } from '@/hooks/useDocumentTitle';
import {
  getNotifications,
  markRead,
  markAllRead,
  deleteNotification,
  type NotificationItem,
} from '@/services/notificationService';

/** Group notifications by date bucket */
function groupByDate(items: NotificationItem[]): Record<string, NotificationItem[]> {
  const groups: Record<string, NotificationItem[]> = {};
  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const yesterday = new Date(today.getTime() - 86400000);

  for (const item of items) {
    const created = new Date(item.created_at);
    const createdDate = new Date(created.getFullYear(), created.getMonth(), created.getDate());
    let label: string;
    if (createdDate.getTime() === today.getTime()) label = 'Today';
    else if (createdDate.getTime() === yesterday.getTime()) label = 'Yesterday';
    else label = createdDate.toLocaleDateString('en-US', { month: 'long', day: 'numeric' });

    if (!groups[label]) groups[label] = [];
    groups[label].push(item);
  }
  return groups;
}

function typeIcon(type: string): string {
  const map: Record<string, string> = {
    recommendation: 'auto_awesome', breaking: 'bolt', trending: 'trending_up',
    digest: 'summarize', system: 'info',
  };
  return map[type] ?? 'notifications';
}

function formatTime(dateStr: string): string {
  return new Date(dateStr).toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' });
}

export default function NotificationsPage() {
  useDocumentTitle('Notifications — NexusAI');

  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [markingAll, setMarkingAll] = useState(false);

  const loadNotifications = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const result = await getNotifications(undefined, 100, 0);
      if (result.success && result.data) setNotifications(result.data.items);
    } catch { setError('Failed to load notifications.'); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { loadNotifications(); }, [loadNotifications]);

  async function handleMarkAllRead() {
    setMarkingAll(true);
    try {
      await markAllRead();
      setNotifications((prev) => prev.map((n) => ({ ...n, status: 'read', read_at: new Date().toISOString() })));
    } catch { /* silent */ }
    finally { setMarkingAll(false); }
  }

  async function handleMarkRead(id: string) {
    try {
      await markRead(id);
      setNotifications((prev) => prev.map((n) => n.id === id ? { ...n, status: 'read', read_at: new Date().toISOString() } : n));
    } catch { /* silent */ }
  }

  async function handleDelete(id: string) {
    try { await deleteNotification(id); setNotifications((prev) => prev.filter((n) => n.id !== id)); }
    catch { /* silent */ }
  }

  const unreadCount = notifications.filter((n) => n.status !== 'read').length;
  const grouped = groupByDate(notifications);

  return (
    <div className="flex flex-col min-h-screen">
      {/* Header */}
      <div className="sticky top-0 z-10 bg-surface/90 backdrop-blur-md border-b border-outline-variant px-4 py-3 flex items-center justify-between">
        <div>
          <h2 className="font-headline font-semibold text-[16px] text-on-surface tracking-tight">Notifications</h2>
          <p className="font-mono text-[10px] text-[var(--c-text-3)] uppercase tracking-wider mt-0.5">
            {unreadCount > 0 ? `${unreadCount} unread` : 'All caught up'}
          </p>
        </div>
        <button
          onClick={handleMarkAllRead}
          disabled={markingAll || unreadCount === 0}
          className="btn-ghost text-[12px] disabled:opacity-40"
        >
          {markingAll ? (
            <span className="w-3.5 h-3.5 border-2 border-transparent border-t-current rounded-full animate-spin" />
          ) : (
            <span className="material-symbols-outlined text-sm">done_all</span>
          )}
          Mark all read
        </button>
      </div>

      <div className="px-4 py-3 space-y-4 pb-24">
        {error && (
          <div className="flex items-center gap-2 text-[var(--c-danger)] p-3 bg-[var(--c-danger-dim)] rounded border border-[var(--c-danger)]/20">
            <span className="material-symbols-outlined text-base">error</span>
            <span className="font-body text-[13px]">{error}</span>
            <button onClick={loadNotifications} className="ml-auto text-[12px] font-mono text-primary uppercase tracking-wider hover:underline bg-transparent border-none cursor-pointer">Retry</button>
          </div>
        )}

        {loading && (
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="card-intel p-4">
                <div className="flex gap-3">
                  <div className="w-8 h-8 rounded bg-[var(--c-elevated)] skeleton-shimmer" />
                  <div className="flex-1 space-y-2">
                    <div className="h-3.5 bg-[var(--c-elevated)] rounded w-2/3 skeleton-shimmer" />
                    <div className="h-3 bg-[var(--c-elevated)] rounded w-full skeleton-shimmer" />
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {!loading && notifications.length === 0 && !error && (
          <div className="flex flex-col items-center justify-center py-20 text-center">
            <div className="w-12 h-12 rounded bg-[var(--c-elevated)] flex items-center justify-center mb-4">
              <span className="material-symbols-outlined text-2xl text-[var(--c-text-3)]">notifications_off</span>
            </div>
            <h3 className="font-headline font-semibold text-[16px] text-on-surface mb-1.5 tracking-tight">No notifications</h3>
            <p className="text-[var(--c-text-2)] font-body text-[13px] max-w-xs">
              Intelligence alerts will appear here when updates match your interests.
            </p>
          </div>
        )}

        {!loading && Object.entries(grouped).map(([dateLabel, items]) => (
          <section key={dateLabel}>
            <div className="flex items-center gap-3 mb-2">
              <h3 className="type-mono-label text-[var(--c-text-3)]">{dateLabel}</h3>
              <div className="flex-1 h-px bg-[var(--c-border-subtle)]" />
            </div>
            <div className="space-y-1.5">
              {items.map((notif) => {
                const isUnread = notif.status !== 'read';
                return (
                  <div
                    key={notif.id}
                    onClick={() => isUnread && handleMarkRead(notif.id)}
                    className={`group relative px-3 py-2.5 rounded flex gap-2.5 items-start transition-all cursor-pointer ${
                      isUnread
                        ? 'bg-[var(--c-accent-dim)] hover:bg-[var(--c-accent-glow)] border border-primary/20'
                        : 'hover:bg-[var(--c-elevated)] border border-transparent'
                    }`}
                  >
                    {isUnread && <div className="absolute top-3 right-3 w-1.5 h-1.5 bg-primary rounded-full" />}

                    <div className={`w-8 h-8 shrink-0 flex items-center justify-center rounded ${
                      isUnread ? 'bg-[var(--c-accent-glow)]' : 'bg-[var(--c-elevated)]'
                    }`}>
                      <span className={`material-symbols-outlined text-base ${isUnread ? 'text-primary' : 'text-[var(--c-text-3)]'}`}>
                        {typeIcon(notif.notification_type)}
                      </span>
                    </div>

                    <div className="flex-1 min-w-0">
                      <div className="flex justify-between items-start">
                        <h4 className={`font-headline text-[13px] leading-snug tracking-tight ${isUnread ? 'font-semibold text-on-surface' : 'text-[var(--c-text-2)]'}`}>
                          {notif.title}
                        </h4>
                        <span className="font-mono text-[10px] text-[var(--c-text-3)] shrink-0 ml-2 tabular-nums">
                          {formatTime(notif.created_at)}
                        </span>
                      </div>
                      <p className={`font-body text-[12px] mt-0.5 leading-relaxed ${isUnread ? 'text-[var(--c-text-2)]' : 'text-[var(--c-text-3)]'}`}>
                        {notif.message}
                      </p>

                      {notif.recommendation_score > 0 && (
                        <span className="badge badge-primary mt-1.5 !text-[8px]">
                          {Math.round(notif.recommendation_score)}% match
                        </span>
                      )}

                      {isUnread && (
                        <div className="flex gap-2 mt-2">
                          <button onClick={(e) => { e.stopPropagation(); handleMarkRead(notif.id); }}
                            className="btn-ghost text-[11px] text-primary !py-1 !px-2">Mark read</button>
                          <button onClick={(e) => { e.stopPropagation(); handleDelete(notif.id); }}
                            className="btn-ghost text-[11px] text-[var(--c-text-3)] !py-1 !px-2">Dismiss</button>
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </section>
        ))}
      </div>
    </div>
  );
}
