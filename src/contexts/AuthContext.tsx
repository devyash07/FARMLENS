import React, { createContext, useContext, useState, useCallback, useEffect } from "react";
import { createClient } from "@supabase/supabase-js";

// Initialize Supabase client (with fallback if not configured)
const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || "";
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY || "";

// Only create Supabase client if both URL and key are configured
export const supabase = (supabaseUrl && supabaseAnonKey) 
  ? createClient(supabaseUrl, supabaseAnonKey)
  : null;

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
  loginWithGoogle: () => Promise<void>;
  logout: () => void;
  updateProfile: (updates: Partial<User & { password?: string }>) => Promise<void>;
  clearError: () => void;
  history: AnalysisRecord[];
  addAnalysis: (record: Omit<AnalysisRecord, "id" | "date">) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [history, setHistory] = useState<AnalysisRecord[]>(() => {
    const saved = localStorage.getItem("farmlens_history");
    return saved ? JSON.parse(saved) : [];
  });

  // Verify and sync Supabase session on mount
  useEffect(() => {
    if (!supabase) {
      const token = localStorage.getItem("farmlens_token");
      if (token) {
        try {
          const userData = JSON.parse(localStorage.getItem("farmlens_user") || "{}");
          if (userData.email) {
            setUser(userData);
          }
        } catch (e) {
          console.warn("[FarmLens] Could not restore local auth session");
        }
      }
      setIsLoading(false);
      return;
    }

    supabase.auth.getSession().then(({ data: { session } }) => {
      if (session?.user) {
        setUser({
          userId: session.user.id,
          email: session.user.email || "",
          name: session.user.user_metadata?.name || session.user.email?.split("@")[0] || "User",
          avatar: session.user.user_metadata?.avatar_url,
        });
        localStorage.setItem("farmlens_token", session.access_token);
      }
      setIsLoading(false);
    });

    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      if (session?.user) {
        setUser({
          userId: session.user.id,
          email: session.user.email || "",
          name: session.user.user_metadata?.name || session.user.email?.split("@")[0] || "User",
          avatar: session.user.user_metadata?.avatar_url,
        });
        localStorage.setItem("farmlens_token", session.access_token);
      } else {
        // Enforce strict logout on auth state change
        setUser(null);
        setHistory([]);
        localStorage.removeItem("farmlens_token");
        localStorage.removeItem("farmlens_user");
        localStorage.removeItem("farmlens_history");
      }
      setIsLoading(false);
    });

    return () => subscription.unsubscribe();
  }, []);

  const clearError = useCallback(() => setError(null), []);

  const login = useCallback(async (email: string, password: string) => {
    setIsLoading(true);
    setError(null);
    try {
      if (supabase) {
        const { error } = await supabase.auth.signInWithPassword({ email, password });
        if (error) throw error;
      } else {
        const response = await fetch(`${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}/api/auth/login`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email, password })
        });
        if (!response.ok) {
          const data = await response.json();
          throw new Error(data.detail || "Login failed");
        }
        const data = await response.json();
        const userData: User = {
          userId: data.user_id,
          email: data.email,
          name: data.name || email.split("@")[0],
        };
        setUser(userData);
        localStorage.setItem("farmlens_token", data.token);
        localStorage.setItem("farmlens_user", JSON.stringify(userData));
      }
      sessionStorage.setItem("farmlens_just_logged_in", "1");
    } catch (err: any) {
      // Smart error handling for Google accounts
      if (err.message.includes("Invalid login credentials")) {
        setError("Invalid password, or this email uses Google Login. Try 'Continue with Google'.");
      } else {
        setError(err.message || "Login failed");
      }
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const register = useCallback(async (name: string, email: string, password: string) => {
    setIsLoading(true);
    setError(null);
    try {
      if (supabase) {
        const { error } = await supabase.auth.signUp({
          email,
          password,
          options: { data: { name } }
        });
        if (error) throw error;
      } else {
        const response = await fetch(`${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}/api/auth/register`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ name, email, password })
        });
        if (!response.ok) {
          const data = await response.json();
          throw new Error(data.detail || "Registration failed");
        }
        const data = await response.json();
        const userData: User = {
          userId: data.user_id,
          email: data.email,
          name: data.name,
        };
        setUser(userData);
        localStorage.setItem("farmlens_token", data.token);
        localStorage.setItem("farmlens_user", JSON.stringify(userData));
      }
      sessionStorage.setItem("farmlens_just_logged_in", "1");
    } catch (err: any) {
      setError(err.message || "Registration failed");
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const loginWithGoogle = useCallback(async () => {
    if (!supabase) {
      setError("Google login not available without Supabase configuration");
      return;
    }
    setIsLoading(true);
    setError(null);
    try {
      const { error } = await supabase.auth.signInWithOAuth({
        provider: 'google',
        options: {
          redirectTo: window.location.origin,
        }
      });
      if (error) throw error;
    } catch (err: any) {
      setError(err.message || "Google login failed");
      setIsLoading(false);
      throw err;
    }
  }, []);

  const logout = useCallback(async () => {
    if (supabase) {
      await supabase.auth.signOut();
    }
    
    // AIRTIGHT LOGOUT: Destroy all local session data
    setUser(null);
    setHistory([]);
    localStorage.removeItem("farmlens_token");
    localStorage.removeItem("farmlens_user");
    localStorage.removeItem("farmlens_history");
    sessionStorage.removeItem("farmlens_uploads"); 
    sessionStorage.removeItem("farmlens_just_logged_in");
  }, []);

  const updateProfile = useCallback(async (updates: Partial<User & { password?: string }>) => {
    setIsLoading(true);
    setError(null);
    try {
      if (updates.password) {
        const { error } = await supabase.auth.updateUser({ password: updates.password });
        if (error) throw error;
      }
      if (updates.name || updates.phone !== undefined) {
        const { error } = await supabase.auth.updateUser({
          data: { name: updates.name, phone: updates.phone }
        });
        if (error) throw error;
        
        setUser(prev => prev ? { ...prev, name: updates.name || prev.name, phone: updates.phone || prev.phone } : null);
      }
    } catch (err: any) {
      setError(err.message || "Profile update failed");
      throw err;
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
        user, isAuthenticated: !!user, isLoading, error,
        login, register, loginWithGoogle, logout, updateProfile, clearError, history, addAnalysis 
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