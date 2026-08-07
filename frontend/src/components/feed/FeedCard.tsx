/**
 * FeedCard — renders a live FeedItem from the backend.
 * Clean, modern card inspired by X's tweet layout.
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

function categoryIcon(category: string): string {
  const map: Record<string, string> = {
    ai_model: 'smart_toy', research: 'biotech', product_launch: 'rocket_launch',
    acquisition: 'handshake', funding: 'payments', regulation: 'gavel',
    open_source: 'code', infrastructure: 'dns', ethics_safety: 'shield',
    robotics: 'precision_manufacturing', other: 'article',
  };
  return map[category] ?? 'article';
}

export function FeedCard({ item, showScore, score, reasons, initialSaved, onUnsave }: FeedCardProps) {
  const [saved, setSaved] = useState(initialSaved ?? false);
  const [saving, setSaving] = useState(false);

  async function handleToggleSave(e: React.MouseEvent) {
    e.stopPropagation();
    if (saving) return;
    setSaving(true);
    try {
      if (saved) { await unsaveArticle(item.id); setSaved(false); onUnsave?.(item.id); }
      else { await saveArticle(item.id); setSaved(true); }
    } catch { /* silent */ }
    finally { setSaving(false); }
  }

  return (
    <article className="px-4 py-3 border-b border-outline hover:bg-[var(--c-raised)] transition-colors duration-150 cursor-default">
      <div className="flex gap-3">
        <div className="w-10 h-10 shrink-0 rounded-full bg-[var(--c-elevated)] flex items-center justify-center">
          <span className="material-symbols-outlined text-on-surface-variant text-lg">{categoryIcon(item.ai_category)}</span>
        </div>

        <div className="flex-1 min-w-0">
          {/* Header */}
          <div className="flex items-center gap-1 text-[15px] leading-5">
            <span className="font-bold text-on-surface truncate">{item.organization}</span>
            <span className="text-on-surface-variant">·</span>
            <span className="text-on-surface-variant text-[13px]">{timeAgo(item.published_at)}</span>
            {showScore && score !== undefined && (
              <span className={`ml-auto text-xs font-medium tabular-nums ${score >= 70 ? 'text-[var(--c-success)]' : 'text-on-surface-variant'}`}>
                {Math.round(score)}% match
              </span>
            )}
          </div>

          {/* Title */}
          <a
            href={item.source_url} target="_blank" rel="noopener noreferrer"
            className="text-[15px] text-on-surface leading-[1.4] mt-0.5 block hover:underline decoration-1 underline-offset-2 no-underline"
          >
            {item.cleaned_title}
          </a>

          {/* Summary */}
          <p className="text-[14px] text-on-surface-variant leading-[1.4] mt-1 line-clamp-2">{item.ai_summary}</p>

          {/* Reasons */}
          {reasons && reasons.length > 0 && (
            <p className="text-[12px] text-on-surface-variant mt-1.5 flex items-center gap-1">
              <span className="material-symbols-outlined text-xs text-primary">auto_awesome</span>
              {reasons.slice(0, 2).join(' · ')}
            </p>
          )}

          {/* Tags */}
          {item.ai_tags.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-2">
              {item.ai_tags.slice(0, 4).map((tag) => (
                <span key={tag} className="text-[12px] text-primary bg-primary/5 px-2 py-0.5 rounded-full">{tag}</span>
              ))}
            </div>
          )}

          {/* Footer */}
          <div className="flex items-center gap-1 mt-2 -ml-2">
            <span className="text-[12px] text-on-surface-variant px-2 py-1">{item.ai_category.replace(/_/g, ' ')}</span>
            <span className="text-on-surface-variant text-[12px]">·</span>
            <span className="text-[12px] text-on-surface-variant truncate max-w-[120px]">{item.source}</span>
            <div className="ml-auto flex items-center">
              <button onClick={handleToggleSave} disabled={saving}
                className={`p-2 rounded-full hover:bg-primary/10 transition-colors bg-transparent border-none cursor-pointer ${saved ? 'text-primary' : 'text-on-surface-variant hover:text-primary'}`}
                title={saved ? 'Remove bookmark' : 'Bookmark'}>
                <span className={`material-symbols-outlined text-[18px] ${saved ? 'icon-fill' : ''}`}>bookmark</span>
              </button>
              <button
                onClick={async (e) => {
                  e.stopPropagation();
                  try {
                    if (navigator.share) await navigator.share({ title: item.cleaned_title, url: item.source_url });
                    else {
                      await navigator.clipboard.writeText(item.source_url);
                      const icon = e.currentTarget.querySelector('.material-symbols-outlined');
                      if (icon) { icon.textContent = 'check'; setTimeout(() => { icon.textContent = 'share'; }, 1500); }
                    }
                  } catch { /* cancelled */ }
                }}
                className="p-2 rounded-full hover:text-primary hover:bg-primary/10 transition-colors bg-transparent border-none cursor-pointer text-on-surface-variant"
                title="Share">
                <span className="material-symbols-outlined text-[18px]">share</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </article>
  );
}
