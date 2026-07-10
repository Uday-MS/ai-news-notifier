/**
 * AuthContext — Global authentication state.
 *
 * On mount: checks localStorage for tokens → calls /auth/me → populates user.
 * Provides: user, isAuthenticated, isLoading, refreshUser(), logout().
 */

import { createContext, useContext, useState, useEffect, useCallback, type ReactNode } from 'react';
import { getCurrentUser, logoutUser, type AuthUser } from '@/services/authService';
import { isAuthenticated as hasTokens } from '@/services/apiClient';

interface AuthContextValue {
  user: AuthUser | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  refreshUser: () => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue>({
  user: null,
  isAuthenticated: false,
  isLoading: true,
  refreshUser: async () => {},
  logout: () => {},
});

export function useAuth() {
  return useContext(AuthContext);
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const refreshUser = useCallback(async () => {
    try {
      const result = await getCurrentUser();
      if (result.success && result.data) {
        setUser(result.data);
      } else {
        setUser(null);
      }
    } catch {
      setUser(null);
    }
  }, []);

  const logout = useCallback(() => {
    setUser(null);
    logoutUser();
  }, []);

  // On mount: rehydrate session from stored tokens
  useEffect(() => {
    async function init() {
      if (hasTokens()) {
        await refreshUser();
      }
      setIsLoading(false);
    }
    init();
  }, [refreshUser]);

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isLoading,
        refreshUser,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}
