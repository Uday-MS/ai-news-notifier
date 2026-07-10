import type { TrendingModel } from '@/types/content';

interface TrendingModelsProps {
  models: TrendingModel[];
}

export function TrendingModels({ models }: TrendingModelsProps) {
  return (
    <div className="bg-surface-container-low rounded-2xl overflow-hidden">
      <h3 className="text-headline-sm font-headline text-on-surface px-4 pt-4 pb-3">
        Trending Models
      </h3>
      <ul className="flex flex-col list-none p-0 m-0">
        {models.map((model) => (
          <li
            key={model.rank}
            className="flex justify-between items-center px-4 py-3 hover:bg-surface-container transition-colors cursor-pointer"
          >
            <div>
              <span className="text-label-sm font-body text-on-surface-variant block uppercase tracking-wider">
                {model.rank}
              </span>
              <span className="text-body-md font-body font-bold text-on-surface">
                {model.name}
              </span>
              <span className="text-label-sm font-body text-on-surface-variant block">
                {model.downloads}
              </span>
            </div>
            <span className="material-symbols-outlined text-on-surface-variant text-xl">
              trending_up
            </span>
          </li>
        ))}
      </ul>
      <button className="w-full px-4 py-3 text-left text-primary text-sm font-body hover:bg-surface-container transition-colors bg-transparent border-none cursor-pointer">
        Show more
      </button>
    </div>
  );
}
