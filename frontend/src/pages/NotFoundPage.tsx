import { useDocumentTitle } from '@/hooks/useDocumentTitle';
import { Link } from 'react-router-dom';

export default function NotFoundPage() {
  useDocumentTitle('404 — NexusAI');

  return (
    <div className="flex min-h-[60vh] items-center justify-center px-4">
      <div className="max-w-md text-center">
        <span className="font-mono text-[72px] font-bold text-primary leading-none tracking-tighter">404</span>
        <h2 className="mt-3 font-headline font-semibold text-[18px] text-on-surface tracking-tight">Page not found</h2>
        <p className="mt-2 text-[13px] text-[var(--c-text-2)] font-body">
          The page you're looking for doesn't exist or has been moved.
        </p>
        <div className="mt-6">
          <Link to="/" className="btn-primary inline-flex py-2.5 px-6 text-[14px] no-underline">
            Go Home
          </Link>
        </div>
      </div>
    </div>
  );
}
