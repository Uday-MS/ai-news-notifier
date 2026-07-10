export interface Organization {
  id: string;
  name: string;
  handle: string;
  description: string;
}

interface SuggestedOrganizationsProps {
  organizations: Organization[];
}

export function SuggestedOrganizations({ organizations }: SuggestedOrganizationsProps) {
  return (
    <div className="bg-surface-container-low rounded-2xl overflow-hidden">
      <h3 className="text-headline-sm font-headline text-on-surface px-4 pt-4 pb-3">
        Who to follow
      </h3>
      <div className="flex flex-col">
        {organizations.map((org) => (
          <div
            key={org.id}
            className="flex items-center gap-3 px-4 py-3 hover:bg-surface-container transition-colors cursor-pointer"
          >
            <div className="w-10 h-10 rounded-full bg-primary flex items-center justify-center shrink-0">
              <span className="text-on-primary font-bold text-sm">
                {org.name.slice(0, 2).toUpperCase()}
              </span>
            </div>
            <div className="flex-1 min-w-0">
              <p className="font-body font-bold text-sm text-on-surface truncate">{org.name}</p>
              <p className="font-body text-sm text-on-surface-variant truncate">{org.handle}</p>
            </div>
            <button className="shrink-0 bg-on-surface text-surface rounded-full px-4 py-1.5 font-bold text-sm border-none cursor-pointer hover:opacity-80 transition-opacity">
              Follow
            </button>
          </div>
        ))}
      </div>
      <button className="w-full px-4 py-3 text-left text-primary text-sm font-body hover:bg-surface-container transition-colors bg-transparent border-none cursor-pointer">
        Show more
      </button>
    </div>
  );
}
