import { lazy, Suspense } from 'react';
import { createBrowserRouter, Navigate, Outlet } from 'react-router-dom';
import { AppLayout } from '@/layouts/AppLayout';
import { AuthLayout } from '@/layouts/AuthLayout';
import { useAuth } from '@/store/AuthContext';

/* ── Eager imports — critical path ────────────────────────────────────── */
import HomePage from '@/pages/HomePage';

/* ── Lazy imports — code-split secondary routes ──────────────────────── */
const NewsPage = lazy(() => import('@/pages/NewsPage'));
const OpportunitiesPage = lazy(() => import('@/pages/OpportunitiesPage'));
const ResearchPage = lazy(() => import('@/pages/ResearchPage'));
const GitHubPage = lazy(() => import('@/pages/GitHubPage'));
const HackathonsPage = lazy(() => import('@/pages/HackathonsPage'));
const SavedPage = lazy(() => import('@/pages/SavedPage'));
const NotificationsPage = lazy(() => import('@/pages/NotificationsPage'));
const ProfilePage = lazy(() => import('@/pages/ProfilePage'));
const SettingsPage = lazy(() => import('@/pages/SettingsPage'));
const LoginPage = lazy(() => import('@/pages/LoginPage'));
const RegisterPage = lazy(() => import('@/pages/RegisterPage'));
const ForgotPasswordPage = lazy(() => import('@/pages/ForgotPasswordPage'));
const ResetPasswordPage = lazy(() => import('@/pages/ResetPasswordPage'));
const NotFoundPage = lazy(() => import('@/pages/NotFoundPage'));
const OnboardingPage = lazy(() => import('@/pages/OnboardingPage'));

/* ── Loading fallback ─────────────────────────────────────────────────── */
function LoadingScreen() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-surface">
      <span className="material-symbols-outlined text-primary text-4xl animate-spin">progress_activity</span>
    </div>
  );
}

function PageSuspense({ children }: { children: React.ReactNode }) {
  return (
    <Suspense fallback={
      <div className="flex items-center justify-center py-20">
        <span className="material-symbols-outlined text-primary text-3xl animate-spin">progress_activity</span>
      </div>
    }>
      {children}
    </Suspense>
  );
}

/** Redirects unauthenticated users to /login. Redirects to /onboarding if not completed. */
function ProtectedRoute() {
  const { isAuthenticated, isLoading, user } = useAuth();

  if (isLoading) return <LoadingScreen />;
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  if (user && !user.onboarding_completed) return <Navigate to="/onboarding" replace />;

  return <Outlet />;
}

/** Only accessible when authenticated AND onboarding is NOT complete. */
function OnboardingRoute() {
  const { isAuthenticated, isLoading, user } = useAuth();

  if (isLoading) return <LoadingScreen />;
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  if (user?.onboarding_completed) return <Navigate to="/" replace />;

  return <Outlet />;
}

/** Redirects authenticated users to / */
function GuestRoute() {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) return <LoadingScreen />;

  return isAuthenticated ? <Navigate to="/" replace /> : <Outlet />;
}

export const router = createBrowserRouter([
  {
    element: <ProtectedRoute />,
    children: [
      {
        element: <AppLayout />,
        children: [
          { path: '/', element: <HomePage /> },
          { path: '/news', element: <PageSuspense><NewsPage /></PageSuspense> },
          { path: '/opportunities', element: <PageSuspense><OpportunitiesPage /></PageSuspense> },
          { path: '/research', element: <PageSuspense><ResearchPage /></PageSuspense> },
          { path: '/github', element: <PageSuspense><GitHubPage /></PageSuspense> },
          { path: '/hackathons', element: <PageSuspense><HackathonsPage /></PageSuspense> },
          { path: '/saved', element: <PageSuspense><SavedPage /></PageSuspense> },
          { path: '/notifications', element: <PageSuspense><NotificationsPage /></PageSuspense> },
          { path: '/profile', element: <PageSuspense><ProfilePage /></PageSuspense> },
          { path: '/settings', element: <PageSuspense><SettingsPage /></PageSuspense> },
          { path: '*', element: <PageSuspense><NotFoundPage /></PageSuspense> },
        ],
      },
    ],
  },
  {
    element: <OnboardingRoute />,
    children: [
      { path: '/onboarding', element: <PageSuspense><OnboardingPage /></PageSuspense> },
    ],
  },
  {
    element: <GuestRoute />,
    children: [
      {
        element: <AuthLayout />,
        children: [
          { path: '/login', element: <PageSuspense><LoginPage /></PageSuspense> },
          { path: '/register', element: <PageSuspense><RegisterPage /></PageSuspense> },
          { path: '/forgot-password', element: <PageSuspense><ForgotPasswordPage /></PageSuspense> },
          { path: '/reset-password', element: <PageSuspense><ResetPasswordPage /></PageSuspense> },
        ],
      },
    ],
  },
]);
