/**
 * TopStories — shows the most important/highest-scoring stories from the backend.
 * Replaces the old mock SuggestedOrganizations widget.
 */

import type { FeedItem } from '@/services/feedService';

interface TopStoriesProps {
  stories: FeedItem[];
}

function timeAgo(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime();
  const minutes = Math.floor(diff / 60000);
  if (minutes < 1) return 'now';
  if (minutes < 60) return `${minutes}m`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h`;
  const days = Math.floor(hours / 24);
  if (days < 7) return `${days}d`;
  return new Date(dateStr).toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

export function TopStories({ stories }: TopStoriesProps) {
  if (stories.length === 0) return null;

  return (
    <div className="bg-[var(--c-raised)] rounded-2xl overflow-hidden">
      <h3 className="font-bold text-xl text-on-surface px-4 pt-3 pb-2">Top Stories</h3>
      <div className="flex flex-col">
        {stories.slice(0, 4).map((story) => (
          <a
            key={story.id}
            href={story.source_url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex gap-3 items-start px-4 py-2.5 hover:bg-[var(--c-elevated)] transition-colors cursor-pointer no-underline"
          >
            <div className="w-8 h-8 shrink-0 rounded-full bg-[var(--c-elevated)] flex items-center justify-center mt-0.5">
              <span className="text-on-surface-variant font-bold text-xs">
                {story.organization.slice(0, 2).toUpperCase()}
              </span>
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-[14px] text-on-surface leading-[1.3] font-medium line-clamp-2">
                {story.cleaned_title}
              </p>
              <p className="text-[12px] text-on-surface-variant mt-0.5">
                {story.organization} · {timeAgo(story.published_at)}
                {story.importance_score > 0 && (
                  <span className="ml-1 text-primary">⚡ {story.importance_score}</span>
                )}
              </p>
            </div>
          </a>
        ))}
      </div>
    </div>
  );
}
