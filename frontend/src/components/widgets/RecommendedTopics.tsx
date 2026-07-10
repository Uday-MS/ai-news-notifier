interface RecommendedTopicsProps {
  topics: string[];
}

export function RecommendedTopics({ topics }: RecommendedTopicsProps) {
  return (
    <div className="bg-surface-container-low rounded-2xl overflow-hidden">
      <h3 className="text-headline-sm font-headline text-on-surface px-4 pt-4 pb-3">
        Recommended Topics
      </h3>
      <div className="flex flex-wrap gap-2 px-4 pb-4">
        {topics.map((topic) => (
          <span
            key={topic}
            className="px-3 py-1.5 bg-surface border border-outline text-sm font-body text-on-surface rounded-full hover:bg-primary-container hover:text-on-primary-container hover:border-primary cursor-pointer transition-colors"
          >
            {topic}
          </span>
        ))}
      </div>
    </div>
  );
}
