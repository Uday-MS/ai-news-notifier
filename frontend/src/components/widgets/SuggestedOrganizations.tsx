/**
 * TopStories — Most important intelligence from the backend.
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
    <div className="card-intel overflow-hidden">
      <div className="px-3 pt-3 pb-2 border-b border-outline-variant">
        <h3 className="type-mono-label text-[var(--c-text-3)]">Top Stories</h3>
      </div>
      <div className="flex flex-col">
        {stories.slice(0, 4).map((story) => (
          <a
            key={story.id}
            href={story.source_url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex gap-2.5 items-start px-3 py-2.5 hover:bg-[var(--c-elevated)] transition-colors cursor-pointer no-underline"
          >
            <div className="flex-1 min-w-0">
              <p className="font-headline font-medium text-[13px] text-on-surface leading-[1.35] line-clamp-2 tracking-tight">
                {story.cleaned_title}
              </p>
              <div className="flex items-center gap-1.5 mt-1">
                <span className="font-mono text-[10px] text-[var(--c-text-3)] uppercase tracking-wider">
                  {story.source}
                </span>
                <span className="text-[var(--c-text-4)]">·</span>
                <span className="font-mono text-[10px] text-[var(--c-text-3)] tabular-nums">
                  {timeAgo(story.published_at)}
                </span>
                {story.importance_score > 0 && (
                  <span className="badge badge-primary ml-auto !h-[16px] !text-[8px]">
                    IMP {story.importance_score}
                  </span>
                )}
              </div>
            </div>
          </a>
        ))}
      </div>
    </div>
  );
}
