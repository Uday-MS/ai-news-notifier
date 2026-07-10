import { useDocumentTitle } from '@/hooks/useDocumentTitle';
import { Link } from 'react-router-dom';

export default function NotFoundPage() {
  useDocumentTitle('404 — Platinum Mist');

  return (
    <div className="flex min-h-[60vh] items-center justify-center px-4">
      <div className="max-w-md text-center">
        <h1 className="text-7xl font-bold font-headline text-primary">404</h1>
        <h2 className="mt-4 text-xl font-semibold font-headline text-primary uppercase">Page not found</h2>
        <p className="mt-2 text-sm text-on-surface-variant font-body">
          The page you're looking for doesn't exist or has been moved.
        </p>
        <div className="mt-6">
          <Link
            to="/"
            className="inline-flex items-center justify-center bg-primary px-6 py-3 text-sm font-headline text-on-primary uppercase tracking-widest hover:bg-primary-container transition-colors no-underline"
          >
            Go Home
          </Link>
        </div>
      </div>
    </div>
  );
}
