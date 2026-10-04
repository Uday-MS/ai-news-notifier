/**
 * FeedCard — Intelligence card for the feed.
 * Instrument-grade design with structured briefing layout.
 */

import { useState } from 'react';
import type { FeedItem } from '@/services/feedService';
import { saveArticle, unsaveArticle } from '@/services/savedService';

interface FeedCardProps {
  item: FeedItem;
  showScore?: boolean;
  score?: number;
  reasons?: string[];
  whyItMatters?: string | null;
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

function ImportanceBar({ score }: { score: number }) {
  const level = score >= 8 ? 5 : score >= 6 ? 4 : score >= 4 ? 3 : score >= 2 ? 2 : 1;
  const variant = score >= 8 ? 'high' : score >= 5 ? 'medium' : '';
  return (
    <div className={`importance-bar ${variant}`} title={`Importance: ${score}/10`}>
      {[1, 2, 3, 4, 5].map((i) => (
        <div key={i} className={`segment ${i <= level ? 'active' : ''}`} />
      ))}
    </div>
  );
}

export function FeedCard({ item, showScore, score, reasons, whyItMatters, initialSaved, onUnsave }: FeedCardProps) {
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
    <article className="px-4 py-3.5 border-b border-outline-variant hover:bg-[var(--c-raised)] transition-colors duration-100 cursor-default">
      {/* Header — Source + Time + Category */}
      <div className="flex items-center gap-2 mb-2">
        <div className="w-7 h-7 shrink-0 rounded bg-[var(--c-elevated)] flex items-center justify-center">
          <span className="material-symbols-outlined text-[var(--c-text-3)] text-sm">{categoryIcon(item.ai_category)}</span>
        </div>
        <div className="flex items-center gap-1.5 min-w-0 flex-1">
          <span className="font-headline font-semibold text-[13px] text-on-surface truncate tracking-tight">
            {item.organization}
          </span>
          <span className="text-[var(--c-text-4)]">·</span>
          <span className="font-mono text-[10px] text-[var(--c-text-3)] tabular-nums uppercase tracking-wider shrink-0">
            {timeAgo(item.published_at)}
          </span>
        </div>
        {showScore && score !== undefined && (
          <span className={`badge ${score >= 70 ? 'badge-primary' : 'badge-neutral'}`}>
            {Math.round(score)}%
          </span>
        )}
        {item.importance_score > 0 && (
          <ImportanceBar score={item.importance_score} />
        )}
      </div>

      {/* Title */}
      <a
        href={item.source_url} target="_blank" rel="noopener noreferrer"
        className="font-headline font-semibold text-[15px] text-on-surface leading-[1.4] block hover:text-primary transition-colors no-underline tracking-tight"
      >
        {item.cleaned_title}
      </a>

      {/* Summary */}
      <p className="text-[13px] text-[var(--c-text-2)] leading-[1.45] mt-1.5 line-clamp-2 font-body">
        {item.ai_summary}
      </p>

      {/* Why It Matters — Indigo accent bar */}
      {whyItMatters && (
        <div className="intel-callout mt-2.5">
          <p className="text-[12px] text-[var(--c-text-2)] leading-[1.45] line-clamp-2 font-body">
            <span className="font-mono text-[10px] text-[var(--c-secondary)] uppercase tracking-wider font-medium mr-1.5">
              WHY IT MATTERS
            </span>
            {whyItMatters}
          </p>
        </div>
      )}

      {/* Recommendation reasons */}
      {reasons && reasons.length > 0 && (
        <p className="text-[11px] text-[var(--c-text-3)] mt-2 flex items-center gap-1 font-mono">
          <span className="material-symbols-outlined text-xs text-primary">auto_awesome</span>
          {reasons.slice(0, 2).join(' · ')}
        </p>
      )}

      {/* Tags + Actions */}
      <div className="flex items-center gap-1.5 mt-2.5">
        {/* Tags */}
        {item.ai_tags.length > 0 && (
          <div className="flex flex-wrap gap-1 flex-1 min-w-0">
            {item.ai_tags.slice(0, 3).map((tag) => (
              <span key={tag} className="badge badge-neutral !text-[9px]">{tag}</span>
            ))}
          </div>
        )}

        {/* Source */}
        <span className="font-mono text-[10px] text-[var(--c-text-4)] uppercase tracking-wider truncate max-w-[80px]">
          {item.source}
        </span>

        {/* Actions */}
        <div className="flex items-center gap-0.5 ml-auto shrink-0">
          <button
            onClick={handleToggleSave}
            disabled={saving}
            className={`p-1.5 rounded hover:bg-primary/10 transition-colors bg-transparent border-none cursor-pointer ${saved ? 'text-primary' : 'text-[var(--c-text-3)] hover:text-primary'}`}
            title={saved ? 'Remove bookmark' : 'Bookmark'}
          >
            <span className={`material-symbols-outlined text-[16px] ${saved ? 'icon-fill' : ''}`}>bookmark</span>
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
            className="p-1.5 rounded hover:text-primary hover:bg-primary/10 transition-colors bg-transparent border-none cursor-pointer text-[var(--c-text-3)]"
            title="Share"
          >
            <span className="material-symbols-outlined text-[16px]">share</span>
          </button>
        </div>
      </div>
    </article>
  );
}
