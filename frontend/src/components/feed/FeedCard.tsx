/**
 * FeedCard — renders a live FeedItem from the backend.
 * Replaces PostCard for API-driven data.
 */

import { useState } from 'react';
import type { FeedItem } from '@/services/feedService';
import { saveArticle, unsaveArticle } from '@/services/savedService';

interface FeedCardProps {
  item: FeedItem;
  showScore?: boolean;
  score?: number;
  reasons?: string[];
  initialSaved?: boolean;
  onUnsave?: (id: string) => void;
}

/** Format relative time from ISO string */
function timeAgo(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime();
  const minutes = Math.floor(diff / 60000);
  if (minutes < 1) return 'Just now';
  if (minutes < 60) return `${minutes}m`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h`;
  const days = Math.floor(hours / 24);
  if (days < 7) return `${days}d`;
  return new Date(dateStr).toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

/** Category to Material icon mapping */
function categoryIcon(category: string): string {
  const map: Record<string, string> = {
    ai_model: 'smart_toy',
    research: 'biotech',
    product_launch: 'rocket_launch',
    acquisition: 'handshake',
    funding: 'payments',
    regulation: 'gavel',
    open_source: 'code',
    infrastructure: 'dns',
    ethics_safety: 'shield',
    robotics: 'precision_manufacturing',
    other: 'article',
  };
  return map[category] ?? 'article';
}

/** Importance score to color class */
function scoreColor(score: number): string {
  if (score >= 80) return 'text-error';
  if (score >= 60) return 'text-primary';
  if (score >= 40) return 'text-secondary';
  return 'text-on-surface-variant';
}

export function FeedCard({ item, showScore, score, reasons, initialSaved, onUnsave }: FeedCardProps) {
  const [saved, setSaved] = useState(initialSaved ?? false);
  const [saving, setSaving] = useState(false);

  async function handleToggleSave(e: React.MouseEvent) {
    e.stopPropagation();
    if (saving) return;
    setSaving(true);
    try {
      if (saved) {
        await unsaveArticle(item.id);
        setSaved(false);
        onUnsave?.(item.id);
      } else {
        await saveArticle(item.id);
        setSaved(true);
      }
    } catch { /* silent */ }
    finally { setSaving(false); }
  }

  return (
    <article className="px-4 py-4 border-b border-outline hover:bg-surface-container-low/50 transition-all duration-200" role="article">
      <div className="flex gap-3">
        {/* Icon */}
        <div className="w-10 h-10 shrink-0 rounded-full bg-surface-container border border-outline flex items-center justify-center">
          <span className="material-symbols-outlined text-primary text-xl">
            {categoryIcon(item.ai_category)}
          </span>
        </div>

        <div className="flex-1 min-w-0">
          {/* Header */}
          <div className="flex items-center gap-1.5 mb-0.5 flex-wrap">
            <span className="font-body font-bold text-[15px] text-on-surface truncate">
              {item.organization}
            </span>
            <span className="text-on-surface-variant text-[13px] font-body">·</span>
            <span className="text-on-surface-variant text-[13px] font-body shrink-0">
              {timeAgo(item.published_at)}
            </span>
            {showScore && score !== undefined && (
              <span className={`ml-auto text-xs font-bold font-label ${scoreColor(score)}`}>
                {Math.round(score)}%
              </span>
            )}
          </div>

          {/* Title */}
          <a
            href={item.source_url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-[15px] font-headline text-on-surface leading-snug mb-1 block hover:underline decoration-1 underline-offset-2 no-underline"
          >
            {item.cleaned_title}
          </a>

          {/* Summary */}
          <p className="text-[14px] font-body text-on-surface-variant leading-relaxed mb-2.5 line-clamp-2">
            {item.ai_summary}
          </p>

          {/* Recommendation reasons */}
          {reasons && reasons.length > 0 && (
            <p className="text-[12px] font-label text-secondary mb-2">
              <span className="material-symbols-outlined text-xs align-middle mr-0.5">auto_awesome</span>
              {reasons.slice(0, 2).join(' · ')}
            </p>
          )}

          {/* Tags */}
          {item.ai_tags.length > 0 && (
            <div className="flex flex-wrap gap-1.5 mb-2">
              {item.ai_tags.slice(0, 4).map((tag) => (
                <span
                  key={tag}
                  className="text-[11px] font-label text-primary bg-primary-container px-2 py-0.5 rounded-full"
                >
                  {tag}
                </span>
              ))}
            </div>
          )}

          {/* Footer: Category + Source + Importance */}
          <div className="flex items-center gap-3 text-on-surface-variant">
            <span className="text-[12px] font-label uppercase tracking-wider text-secondary">
              {item.ai_category.replace(/_/g, ' ')}
            </span>
            <span className="text-[12px] font-body truncate max-w-[150px]">
              {item.source}
            </span>
            <div className="ml-auto flex items-center gap-3">
              <button
                onClick={handleToggleSave}
                disabled={saving}
                className={`flex items-center gap-1 p-1.5 rounded-full hover:bg-primary/10 transition-colors bg-transparent border-none cursor-pointer ${saved ? 'text-primary' : 'text-inherit hover:text-primary'}`}
              >
                <span className={`material-symbols-outlined text-[16px] ${saved ? 'icon-fill' : ''}`}>bookmark</span>
              </button>
              <button
                onClick={async (e) => {
                  e.stopPropagation();
                  try {
                    if (navigator.share) {
                      await navigator.share({ title: item.cleaned_title, url: item.source_url });
                    } else {
                      await navigator.clipboard.writeText(item.source_url);
                      const btn = e.currentTarget;
                      const icon = btn.querySelector('.material-symbols-outlined');
                      if (icon) { icon.textContent = 'check'; setTimeout(() => { icon.textContent = 'ios_share'; }, 1500); }
                    }
                  } catch { /* user cancelled */ }
                }}
                className="flex items-center gap-1 p-1.5 rounded-full hover:text-primary hover:bg-primary/10 transition-colors bg-transparent border-none cursor-pointer text-inherit"
              >
                <span className="material-symbols-outlined text-[16px]">ios_share</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </article>
  );
}
