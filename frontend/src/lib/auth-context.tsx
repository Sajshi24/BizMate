import React, { createContext, useContext, useEffect, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import type { LoginCredentials, RegisterData, User } from "@/types";
import {
  clearStoredAuth,
  getCurrentUserApi,
  getStoredToken,
  getStoredUser,
  loginApi,
  logoutApi,
  registerApi,
  setStoredToken,
  setStoredUser,
} from "@/services/api";

interface AuthContextType {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (credentials: LoginCredentials) => Promise<User>;
  register: (data: RegisterData) => Promise<User>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const queryClient = useQueryClient();
  const [user, setUser] = useState<User | null>(() => getStoredUser());
  const [token, setToken] = useState<string | null>(() => getStoredToken());
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;

    async function initAuth() {
      const storedToken = getStoredToken();
      const storedUser = getStoredUser();

      if (storedToken) {
        setToken(storedToken);
        if (storedUser) setUser(storedUser);

        try {
          // Verify and refresh user details from backend
          const freshUser = await getCurrentUserApi(storedToken);
          if (isMounted) {
            setUser(freshUser);
            setStoredUser(freshUser);
          }
        } catch (err: unknown) {
          // Only reset auth if the token is definitively rejected by the backend (401 or 403)
          // Network errors or backend connection timeouts should preserve the local session
          const status = (err as { status?: number })?.status;
          if (status === 401 || status === 403) {
            if (isMounted) {
              clearStoredAuth();
              setToken(null);
              setUser(null);
            }
          }
        }
      } else {
        if (isMounted) {
          setUser(null);
          setToken(null);
        }
      }

      if (isMounted) {
        setIsLoading(false);
      }
    }

    initAuth();

    return () => {
      isMounted = false;
    };
  }, []);

  const login = async (credentials: LoginCredentials): Promise<User> => {
    queryClient.clear();
    const response = await loginApi(credentials);
    setStoredToken(response.access_token);
    setStoredUser(response.user);
    setToken(response.access_token);
    setUser(response.user);
    return response.user;
  };

  const register = async (data: RegisterData): Promise<User> => {
    queryClient.clear();
    const response = await registerApi(data);
    setStoredToken(response.access_token);
    setStoredUser(response.user);
    setToken(response.access_token);
    setUser(response.user);
    return response.user;
  };

  const logout = () => {
    queryClient.clear();
    logoutApi();
    clearStoredAuth();
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated: !!token && !!user,
        isLoading,
        login,
        register,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
