import type { DeadlineItem } from '@/types/content';

interface UpcomingDeadlinesProps {
  deadlines: DeadlineItem[];
}

export function UpcomingDeadlines({ deadlines }: UpcomingDeadlinesProps) {
  return (
    <div className="bg-surface-container-low rounded-2xl overflow-hidden">
      <h3 className="text-headline-sm font-bold text-on-surface px-4 pt-4 pb-3">
        Upcoming Deadlines
      </h3>
      <div className="flex flex-col">
        {deadlines.map((item) => (
          <div
            key={item.title}
            className="flex gap-3 items-center px-4 py-3 hover:bg-surface-container transition-colors cursor-pointer"
          >
            <div className="flex flex-col items-center justify-center w-11 h-11 bg-primary-container text-on-primary-container rounded-lg shrink-0">
              <span className="font-bold text-base leading-none">{item.day}</span>
              <span className="font-body text-[10px] uppercase">{item.month}</span>
            </div>
            <div className="min-w-0">
              <h4 className="font-body font-bold text-sm text-on-surface truncate">{item.title}</h4>
              <span className="font-body text-sm text-on-surface-variant">{item.subtitle}</span>
            </div>
          </div>
        ))}
      </div>
      <button className="w-full px-4 py-3 text-left text-primary text-sm font-body hover:bg-surface-container transition-colors bg-transparent border-none cursor-pointer">
        Show more
      </button>
    </div>
  );
}
