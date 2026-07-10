import { useDocumentTitle } from '@/hooks/useDocumentTitle';
import { ComposeArea } from '@/components/feed/ComposeArea';
import { PostCard } from '@/components/feed/PostCard';
import { POSTS } from '@/utils/mockData';

export default function HomePage() {
  useDocumentTitle('Home — AI News Notifier');

  return (
    <div className="flex flex-col min-h-screen">
      {/* Sticky Header */}
      <div className="sticky top-0 z-10 bg-surface/80 backdrop-blur-md border-b border-outline">
        <div className="flex">
          <button className="flex-1 py-3.5 text-center text-[15px] font-body font-bold text-on-surface hover:bg-surface-container transition-colors bg-transparent border-none cursor-pointer relative">
            For You
            <span className="absolute bottom-0 left-1/2 -translate-x-1/2 w-14 h-1 bg-primary rounded-full" />
          </button>
          <button className="flex-1 py-3.5 text-center text-[15px] font-body text-on-surface-variant hover:bg-surface-container transition-colors bg-transparent border-none cursor-pointer">
            Following
          </button>
        </div>
      </div>

      {/* Compose */}
      <ComposeArea />

      {/* Feed */}
      <div className="flex flex-col page-transition">
        {POSTS.map((post) => (
          <PostCard key={post.id} post={post} />
        ))}
      </div>
    </div>
  );
}
