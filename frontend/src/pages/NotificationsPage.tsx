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

/** Notification type → Material icon */
function typeIcon(type: string): string {
  const map: Record<string, string> = {
    recommendation: 'auto_awesome',
    breaking: 'bolt',
    trending: 'trending_up',
    digest: 'summarize',
    system: 'info',
  };
  return map[type] ?? 'notifications';
}

/** Format time from ISO string */
function formatTime(dateStr: string): string {
  return new Date(dateStr).toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' });
}

export default function NotificationsPage() {
  useDocumentTitle('Notifications — AI News Notifier');

  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [markingAll, setMarkingAll] = useState(false);

  const loadNotifications = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const result = await getNotifications(undefined, 100, 0);
      if (result.success && result.data) {
        setNotifications(result.data.items);
      }
    } catch {
      setError('Failed to load notifications.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadNotifications();
  }, [loadNotifications]);

  async function handleMarkAllRead() {
    setMarkingAll(true);
    try {
      await markAllRead();
      setNotifications((prev) =>
        prev.map((n) => ({ ...n, status: 'read', read_at: new Date().toISOString() }))
      );
    } catch {
      // silent
    } finally {
      setMarkingAll(false);
    }
  }

  async function handleMarkRead(id: string) {
    try {
      await markRead(id);
      setNotifications((prev) =>
        prev.map((n) => n.id === id ? { ...n, status: 'read', read_at: new Date().toISOString() } : n)
      );
    } catch {
      // silent
    }
  }

  async function handleDelete(id: string) {
    try {
      await deleteNotification(id);
      setNotifications((prev) => prev.filter((n) => n.id !== id));
    } catch {
      // silent
    }
  }

  const unreadCount = notifications.filter((n) => n.status !== 'read').length;
  const grouped = groupByDate(notifications);

  return (
    <div className="p-8 md:p-[64px]">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between border-b-2 border-primary pb-6 mb-12">
        <div>
          <h2 className="font-headline text-5xl md:text-7xl text-primary uppercase tracking-wide leading-none">
            Notifications
          </h2>
          <p className="font-label text-secondary mt-2">
            {unreadCount > 0 ? `${unreadCount} UNREAD` : 'ALL CAUGHT UP'}
          </p>
        </div>
        <button
          onClick={handleMarkAllRead}
          disabled={markingAll || unreadCount === 0}
          className="mt-6 md:mt-0 px-6 py-2 border border-primary text-primary font-label uppercase hover:bg-primary hover:text-on-primary transition-colors flex items-center gap-2 bg-transparent cursor-pointer disabled:opacity-50"
        >
          {markingAll ? (
            <span className="w-4 h-4 border-2 border-transparent border-t-current rounded-full animate-spin" />
          ) : (
            <span className="material-symbols-outlined text-sm">done_all</span>
          )}
          Mark all as read
        </button>
      </div>

      <div className="max-w-4xl mx-auto space-y-12 pb-24">
        {/* Error */}
        {error && (
          <div className="flex items-center gap-2 text-error p-4 bg-error-container/30 rounded">
            <span className="material-symbols-outlined text-lg">error</span>
            <span className="font-body text-sm">{error}</span>
            <button
              onClick={loadNotifications}
              className="ml-auto text-sm font-body text-primary hover:underline bg-transparent border-none cursor-pointer"
            >
              Retry
            </button>
          </div>
        )}

        {/* Loading skeleton */}
        {loading && (
          <div className="space-y-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="p-6 border border-outline rounded animate-pulse">
                <div className="flex gap-6">
                  <div className="w-12 h-12 rounded bg-surface-container" />
                  <div className="flex-1 space-y-2">
                    <div className="h-4 bg-surface-container rounded w-1/3" />
                    <div className="h-3 bg-surface-container rounded w-full" />
                    <div className="h-3 bg-surface-container rounded w-2/3" />
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Empty state */}
        {!loading && notifications.length === 0 && !error && (
          <div className="flex flex-col items-center justify-center py-20 text-center">
            <span className="material-symbols-outlined text-6xl text-on-surface-variant mb-4">
              notifications_off
            </span>
            <h3 className="text-xl font-headline text-on-surface mb-2 uppercase">No Notifications</h3>
            <p className="text-on-surface-variant font-body text-sm max-w-xs">
              Your notifications will appear here when there are new AI intelligence updates matching your interests.
            </p>
          </div>
        )}

        {/* Grouped notifications */}
        {!loading &&
          Object.entries(grouped).map(([dateLabel, items]) => (
            <section key={dateLabel}>
              <div className="flex items-center gap-4 mb-6">
                <h3
                  className={`font-label text-xl uppercase tracking-widest ${
                    dateLabel === 'Today' ? 'text-primary font-bold' : 'text-secondary'
                  }`}
                >
                  {dateLabel}
                </h3>
                <div className="flex-1 h-px bg-outline-variant" />
              </div>
              <div className="space-y-4">
                {items.map((notif) => {
                  const isUnread = notif.status !== 'read';
                  return (
                    <div
                      key={notif.id}
                      onClick={() => isUnread && handleMarkRead(notif.id)}
                      className={`group relative p-6 rounded flex flex-col sm:flex-row gap-6 items-start transition-all cursor-pointer ${
                        isUnread
                          ? 'bg-surface-container-lowest border-2 border-primary hover:shadow-[4px_4px_0px_#16191e]'
                          : 'bg-surface border border-outline opacity-80 hover:opacity-100'
                      }`}
                    >
                      {/* Unread diamond */}
                      {isUnread && (
                        <div className="absolute top-0 right-0 w-3 h-3 bg-primary transform translate-x-1.5 -translate-y-1.5 rotate-45" />
                      )}

                      {/* Icon */}
                      <div
                        className={`w-12 h-12 shrink-0 border flex items-center justify-center rounded-sm ${
                          isUnread
                            ? 'bg-surface-container border-outline'
                            : 'bg-surface-container-lowest border-outline-variant'
                        }`}
                      >
                        <span
                          className={`material-symbols-outlined ${
                            isUnread ? 'text-primary' : 'text-secondary'
                          }`}
                        >
                          {typeIcon(notif.notification_type)}
                        </span>
                      </div>

                      {/* Content */}
                      <div className="flex-1 min-w-0">
                        <div className="flex justify-between items-start mb-2">
                          <h4
                            className={`font-headline text-lg uppercase ${
                              isUnread ? 'text-primary text-2xl' : 'text-secondary text-xl'
                            }`}
                          >
                            {notif.title}
                          </h4>
                          <span
                            className={`font-label text-sm shrink-0 ml-4 ${
                              isUnread ? 'text-secondary' : 'text-tertiary'
                            }`}
                          >
                            {formatTime(notif.created_at)}
                          </span>
                        </div>
                        <p
                          className={`font-body max-w-2xl ${
                            isUnread ? 'text-lg text-on-surface-variant mb-4' : 'text-base text-secondary'
                          }`}
                        >
                          {notif.message}
                        </p>

                        {/* Score badge */}
                        {notif.recommendation_score > 0 && (
                          <span className="inline-flex items-center gap-1 text-xs font-label text-primary bg-primary-container px-2 py-0.5 rounded-full mr-2">
                            <span className="material-symbols-outlined text-xs">star</span>
                            {Math.round(notif.recommendation_score)}% match
                          </span>
                        )}

                        {/* Actions */}
                        {isUnread && (
                          <div className="flex gap-3 mt-3">
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                handleMarkRead(notif.id);
                              }}
                              className="px-4 py-1.5 bg-primary text-on-primary font-label text-sm uppercase hover:bg-tertiary transition-colors border-none cursor-pointer"
                            >
                              Mark Read
                            </button>
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                handleDelete(notif.id);
                              }}
                              className="px-4 py-1.5 border border-outline text-secondary font-label text-sm uppercase hover:bg-surface-container transition-colors bg-transparent cursor-pointer"
                            >
                              Dismiss
                            </button>
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
