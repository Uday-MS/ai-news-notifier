import { createBrowserRouter, Navigate, Outlet } from 'react-router-dom';
import { AppLayout } from '@/layouts/AppLayout';
import { AuthLayout } from '@/layouts/AuthLayout';
import { useAuth } from '@/store/AuthContext';

import HomePage from '@/pages/HomePage';
import NewsPage from '@/pages/NewsPage';
import OpportunitiesPage from '@/pages/OpportunitiesPage';
import ResearchPage from '@/pages/ResearchPage';
import GitHubPage from '@/pages/GitHubPage';
import HackathonsPage from '@/pages/HackathonsPage';
import SavedPage from '@/pages/SavedPage';
import NotificationsPage from '@/pages/NotificationsPage';
import ProfilePage from '@/pages/ProfilePage';
import SettingsPage from '@/pages/SettingsPage';
import LoginPage from '@/pages/LoginPage';
import RegisterPage from '@/pages/RegisterPage';
import ForgotPasswordPage from '@/pages/ForgotPasswordPage';
import ResetPasswordPage from '@/pages/ResetPasswordPage';
import NotFoundPage from '@/pages/NotFoundPage';
import OnboardingPage from '@/pages/OnboardingPage';

function LoadingScreen() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-surface">
      <span className="material-symbols-outlined text-primary text-4xl animate-spin">progress_activity</span>
    </div>
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
          { path: '/news', element: <NewsPage /> },
          { path: '/opportunities', element: <OpportunitiesPage /> },
          { path: '/research', element: <ResearchPage /> },
          { path: '/github', element: <GitHubPage /> },
          { path: '/hackathons', element: <HackathonsPage /> },
          { path: '/saved', element: <SavedPage /> },
          { path: '/notifications', element: <NotificationsPage /> },
          { path: '/profile', element: <ProfilePage /> },
          { path: '/settings', element: <SettingsPage /> },
          { path: '*', element: <NotFoundPage /> },
        ],
      },
    ],
  },
  {
    element: <OnboardingRoute />,
    children: [
      { path: '/onboarding', element: <OnboardingPage /> },
    ],
  },
  {
    element: <GuestRoute />,
    children: [
      {
        element: <AuthLayout />,
        children: [
          { path: '/login', element: <LoginPage /> },
          { path: '/register', element: <RegisterPage /> },
          { path: '/forgot-password', element: <ForgotPasswordPage /> },
          { path: '/reset-password', element: <ResetPasswordPage /> },
        ],
      },
    ],
  },
]);
