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
    <div className="flex flex-col min-h-screen">
      {/* Header */}
      <div className="sticky top-0 z-10 bg-surface/95 backdrop-blur-md border-b border-outline px-4 py-3 flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold font-body text-on-surface">Notifications</h2>
          <p className="text-xs text-on-surface-variant font-body mt-0.5">
            {unreadCount > 0 ? `${unreadCount} unread` : 'All caught up'}
          </p>
        </div>
        <button
          onClick={handleMarkAllRead}
          disabled={markingAll || unreadCount === 0}
          className="px-4 py-1.5 rounded-full border border-outline text-on-surface font-body font-bold text-sm hover:bg-surface-container transition-colors flex items-center gap-1.5 bg-transparent cursor-pointer disabled:opacity-50"
        >
          {markingAll ? (
            <span className="w-4 h-4 border-2 border-transparent border-t-current rounded-full animate-spin" />
          ) : (
            <span className="material-symbols-outlined text-sm">done_all</span>
          )}
          Mark all as read
        </button>
      </div>

      <div className="px-4 py-4 space-y-6 pb-24">
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
            <h3 className="text-xl font-bold text-on-surface mb-2">No Notifications</h3>
            <p className="text-on-surface-variant font-body text-sm max-w-xs">
              Your notifications will appear here when there are new AI intelligence updates matching your interests.
            </p>
          </div>
        )}

        {/* Grouped notifications */}
        {!loading &&
          Object.entries(grouped).map(([dateLabel, items]) => (
            <section key={dateLabel}>
              <div className="flex items-center gap-3 mb-3">
                <h3
                  className={`font-body text-sm font-bold ${
                    dateLabel === 'Today' ? 'text-on-surface' : 'text-on-surface-variant'
                  }`}
                >
                  {dateLabel}
                </h3>
                <div className="flex-1 h-px bg-outline" />
              </div>
              <div className="space-y-2">
                {items.map((notif) => {
                  const isUnread = notif.status !== 'read';
                  return (
                    <div
                      key={notif.id}
                      onClick={() => isUnread && handleMarkRead(notif.id)}
                      className={`group relative px-4 py-3 rounded-xl flex gap-3 items-start transition-all cursor-pointer ${
                        isUnread
                          ? 'bg-primary-container/30 hover:bg-primary-container/50'
                          : 'hover:bg-surface-container-low/50'
                      }`}
                    >
                      {/* Unread dot */}
                      {isUnread && (
                        <div className="absolute top-4 right-3 w-2 h-2 bg-primary rounded-full" />
                      )}

                      {/* Icon */}
                      <div
                        className={`w-10 h-10 shrink-0 flex items-center justify-center rounded-full ${
                          isUnread
                            ? 'bg-primary-container'
                            : 'bg-surface-container'
                        }`}
                      >
                        <span
                          className={`material-symbols-outlined text-lg ${
                            isUnread ? 'text-primary' : 'text-on-surface-variant'
                          }`}
                        >
                          {typeIcon(notif.notification_type)}
                        </span>
                      </div>

                      <div className="flex-1 min-w-0">
                        <div className="flex justify-between items-start">
                          <h4
                            className={`font-body text-[15px] leading-snug ${
                              isUnread ? 'font-bold text-on-surface' : 'text-on-surface-variant'
                            }`}
                          >
                            {notif.title}
                          </h4>
                          <span
                            className={`font-body text-xs shrink-0 ml-3 ${
                              isUnread ? 'text-on-surface-variant' : 'text-on-surface-variant/60'
                            }`}
                          >
                            {formatTime(notif.created_at)}
                          </span>
                        </div>
                        <p
                          className={`font-body text-sm mt-0.5 ${
                            isUnread ? 'text-on-surface-variant' : 'text-on-surface-variant/70'
                          }`}
                        >
                          {notif.message}
                        </p>

                        {/* Score badge */}
                        {notif.recommendation_score > 0 && (
                          <span className="inline-flex items-center gap-1 text-xs font-body text-primary bg-primary-container px-2 py-0.5 rounded-full mt-1">
                            <span className="material-symbols-outlined text-xs">star</span>
                            {Math.round(notif.recommendation_score)}% match
                          </span>
                        )}

                        {isUnread && (
                          <div className="flex gap-2 mt-2">
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                handleMarkRead(notif.id);
                              }}
                              className="px-3 py-1 bg-transparent text-primary font-body text-xs font-bold hover:bg-primary-container/50 transition-colors border-none cursor-pointer rounded-full"
                            >
                              Mark read
                            </button>
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                handleDelete(notif.id);
                              }}
                              className="px-3 py-1 bg-transparent text-on-surface-variant font-body text-xs hover:bg-surface-container transition-colors border-none cursor-pointer rounded-full"
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
