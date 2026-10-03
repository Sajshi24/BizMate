import React, { createContext, useContext, useEffect, useState } from "react";
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
        } catch {
          // If token verification fails (e.g., token expired), reset auth
          if (isMounted) {
            clearStoredAuth();
            setToken(null);
            setUser(null);
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
    const response = await loginApi(credentials);
    setStoredToken(response.access_token);
    setStoredUser(response.user);
    setToken(response.access_token);
    setUser(response.user);
    return response.user;
  };

  const register = async (data: RegisterData): Promise<User> => {
    const response = await registerApi(data);
    setStoredToken(response.access_token);
    setStoredUser(response.user);
    setToken(response.access_token);
    setUser(response.user);
    return response.user;
  };

  const logout = () => {
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
