import React, { createContext, useContext, useState, useCallback, useEffect } from "react";
import { useNavigate } from "react-router-dom";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export interface User {
  name: string;
  email: string;
  userId?: string;
  phone?: string;
  avatar?: string;
}

export interface AnalysisRecord {
  id: string;
  imageName: string;
  imagePreview?: string;
  crop?: string;
  disease: string;
  severity: number;
  confidence: number;
  date: string;
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  login: (email: string, password: string) => Promise<void>;
  register: (name: string, email: string, password: string) => Promise<void>;
  logout: () => void;
  updateProfile: (updates: Partial<User & { password?: string }>) => Promise<void>;
  clearError: () => void;
  history: AnalysisRecord[];
  addAnalysis: (record: Omit<AnalysisRecord, "id" | "date">) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Token management
const TOKEN_KEY = "farmlens_token";
const USER_KEY = "farmlens_user";

function saveToken(token: string) {
  localStorage.setItem(TOKEN_KEY, token);
}

function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
}

function saveUser(user: User) {
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

function getStoredUser(): User | null {
  const saved = localStorage.getItem(USER_KEY);
  return saved ? JSON.parse(saved) : null;
}

function clearUser() {
  localStorage.removeItem(USER_KEY);
}

// API helper with auth token
async function apiCall(endpoint: string, options: RequestInit = {}) {
  const token = getToken();
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...options.headers,
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Request failed' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(getStoredUser);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [history, setHistory] = useState<AnalysisRecord[]>(() => {
    const saved = localStorage.getItem("farmlens_history");
    return saved ? JSON.parse(saved) : [];
  });

  // Verify token on mount
  useEffect(() => {
    const verifyToken = async () => {
      const token = getToken();
      const storedUser = getStoredUser();

      if (token && storedUser) {
        try {
          // Verify token is still valid
          const userData = await apiCall('/api/auth/me');
          setUser(userData);
          saveUser(userData);
        } catch (err) {
          // Token is invalid, clear auth
          console.error('[Auth] Token verification failed:', err);
          clearToken();
          clearUser();
          setUser(null);
        }
      }
    };

    verifyToken();
  }, []);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    setIsLoading(true);
    setError(null);

    try {
      const data = await apiCall('/api/auth/login', {
        method: 'POST',
        body: JSON.stringify({ email, password }),
      });

      saveToken(data.access_token);
      saveUser(data.user);
      setUser(data.user);
      sessionStorage.setItem("farmlens_just_logged_in", "1");
      
      console.log('[Auth] Login successful:', data.user.email);
    } catch (err: any) {
      const errorMsg = err.message || 'Login failed';
      setError(errorMsg);
      console.error('[Auth] Login error:', errorMsg);
      throw new Error(errorMsg);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const register = useCallback(async (name: string, email: string, password: string) => {
    setIsLoading(true);
    setError(null);

    try {
      const data = await apiCall('/api/auth/register', {
        method: 'POST',
        body: JSON.stringify({ name, email, password }),
      });

      saveToken(data.access_token);
      saveUser(data.user);
      setUser(data.user);
      sessionStorage.setItem("farmlens_just_logged_in", "1");
      
      console.log('[Auth] Registration successful:', data.user.email);
    } catch (err: any) {
      const errorMsg = err.message || 'Registration failed';
      setError(errorMsg);
      console.error('[Auth] Registration error:', errorMsg);
      throw new Error(errorMsg);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const logout = useCallback(() => {
    // Call logout endpoint for logging purposes
    const token = getToken();
    if (token) {
      apiCall('/api/auth/logout', { method: 'POST' }).catch(err => {
        console.warn('[Auth] Logout endpoint failed:', err);
      });
    }

    // Clear local state
    clearToken();
    clearUser();
    setUser(null);
    setError(null);
    
    console.log('[Auth] User logged out');
  }, []);

  const updateProfile = useCallback(async (updates: Partial<User & { password?: string }>) => {
    setIsLoading(true);
    setError(null);

    try {
      if (updates.password) {
        // Handle password change separately
        await apiCall('/api/auth/change-password', {
          method: 'POST',
          body: JSON.stringify({
            current_password: '', // Frontend should collect this
            new_password: updates.password,
          }),
        });
      }

      if (updates.name || updates.phone !== undefined) {
        const profileData = await apiCall('/api/auth/profile', {
          method: 'PUT',
          body: JSON.stringify({
            name: updates.name,
            phone: updates.phone,
          }),
        });

        setUser(prev => {
          if (!prev) return prev;
          const updated = { ...prev, ...profileData };
          saveUser(updated);
          return updated;
        });
      }

      console.log('[Auth] Profile updated successfully');
    } catch (err: any) {
      const errorMsg = err.message || 'Profile update failed';
      setError(errorMsg);
      console.error('[Auth] Profile update error:', errorMsg);
      throw new Error(errorMsg);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const addAnalysis = useCallback((record: Omit<AnalysisRecord, "id" | "date">) => {
    const newRecord: AnalysisRecord = {
      ...record,
      id: crypto.randomUUID(),
      date: new Date().toISOString(),
      imagePreview: undefined,
    };

    setHistory(prev => {
      const updated = [newRecord, ...prev].slice(0, 50);
      try {
        localStorage.setItem("farmlens_history", JSON.stringify(updated));
      } catch (e) {
        console.warn("[FarmLens] Storage quota exceeded, trimming history");
        const trimmed = updated.slice(0, 20);
        try {
          localStorage.setItem("farmlens_history", JSON.stringify(trimmed));
          return trimmed;
        } catch {
          console.error("[FarmLens] Unable to save history");
        }
      }
      return updated;
    });
  }, []);

  return (
    <AuthContext.Provider 
      value={{ 
        user, 
        isAuthenticated: !!user, 
        isLoading,
        error,
        login, 
        register, 
        logout, 
        updateProfile,
        clearError,
        history, 
        addAnalysis 
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
};
