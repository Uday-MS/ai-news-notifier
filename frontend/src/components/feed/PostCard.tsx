import type { Post } from '@/types/content';

interface PostCardProps {
  post: Post;
}

export function PostCard({ post }: PostCardProps) {
  const { author, content, codeBlock, image, imageAlt, timestamp, comments, reposts, likes } = post;

  return (
    <article className="px-4 py-3 border-b border-outline hover:bg-surface-container-low/50 transition-colors cursor-pointer">
      <div className="flex gap-3">
        {/* Avatar */}
        {author.avatar ? (
          <div className="w-10 h-10 shrink-0 rounded-full overflow-hidden bg-surface-container">
            <img className="w-full h-full object-cover" alt={author.name} src={author.avatar} />
          </div>
        ) : (
          <div className="w-10 h-10 shrink-0 rounded-full bg-primary text-on-primary flex items-center justify-center font-bold text-sm">
            {author.initials}
          </div>
        )}

        <div className="flex-1 min-w-0">
          {/* Author Info */}
          <div className="flex items-center gap-1 mb-0.5">
            <span className="font-body font-bold text-[15px] text-on-surface truncate">{author.name}</span>
            <span className="text-on-surface-variant text-[15px] font-body truncate">{author.handle}</span>
            <span className="text-on-surface-variant text-[15px] font-body">·</span>
            <span className="text-on-surface-variant text-[15px] font-body shrink-0">{timestamp}</span>
          </div>

          {/* Content */}
          <p className="text-[15px] font-body text-on-surface leading-relaxed mb-3 whitespace-pre-wrap">{content}</p>

          {/* Code Block */}
          {codeBlock && (
            <div className="border border-outline rounded-xl p-3 bg-surface-container mb-3 font-mono text-sm text-on-surface-variant whitespace-pre-line">
              {codeBlock}
            </div>
          )}

          {/* Image */}
          {image && (
            <div className="mb-3 border border-outline overflow-hidden rounded-2xl">
              <img
                className="w-full h-64 object-cover hover:opacity-95 transition-opacity"
                alt={imageAlt ?? ''}
                src={image}
              />
            </div>
          )}

          {/* Actions */}
          <div className="flex justify-between max-w-[425px] -ml-2 text-on-surface-variant">
            <button className="flex items-center gap-1 p-2 rounded-full hover:text-primary hover:bg-primary/10 transition-colors bg-transparent border-none cursor-pointer text-inherit group">
              <span className="material-symbols-outlined text-[18px]">chat_bubble</span>
              <span className="text-[13px] font-body group-hover:text-primary">{comments}</span>
            </button>
            <button className="flex items-center gap-1 p-2 rounded-full hover:text-[#00ba7c] hover:bg-[#00ba7c]/10 transition-colors bg-transparent border-none cursor-pointer text-inherit group">
              <span className="material-symbols-outlined text-[18px]">cached</span>
              <span className="text-[13px] font-body group-hover:text-[#00ba7c]">{reposts}</span>
            </button>
            <button className="flex items-center gap-1 p-2 rounded-full hover:text-[#f91880] hover:bg-[#f91880]/10 transition-colors bg-transparent border-none cursor-pointer text-inherit group">
              <span className="material-symbols-outlined text-[18px]">favorite</span>
              <span className="text-[13px] font-body group-hover:text-[#f91880]">{likes}</span>
            </button>
            <button className="flex items-center gap-1 p-2 rounded-full hover:text-primary hover:bg-primary/10 transition-colors bg-transparent border-none cursor-pointer text-inherit">
              <span className="material-symbols-outlined text-[18px]">ios_share</span>
            </button>
          </div>
        </div>
      </div>
    </article>
  );
}
