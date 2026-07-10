import { useEffect } from 'react';

/**
 * Sets the document title. Restores default on unmount.
 */
export function useDocumentTitle(title: string): void {
  useEffect(() => {
    const prevTitle = document.title;
    document.title = title;
    return () => {
      document.title = prevTitle;
    };
  }, [title]);
}
