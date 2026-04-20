import React, { createContext, useContext, useState, useCallback } from "react";

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
  login: (email: string, password: string) => void;
  register: (name: string, email: string, password: string) => void;
  logout: () => void;
  updateProfile: (updates: Partial<User & { password?: string }>) => void;
  history: AnalysisRecord[];
  addAnalysis: (record: Omit<AnalysisRecord, "id" | "date">) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

/** Minimal JWT builder — HS256 using Web Crypto (no library needed) */
async function buildJWT(userId: string, email: string): Promise<string> {
  const header = btoa(JSON.stringify({ alg: "HS256", typ: "JWT" })).replace(/=/g, "");
  const now = Math.floor(Date.now() / 1000);
  const payload = btoa(JSON.stringify({ sub: userId, email, iat: now, exp: now + 86400 * 7 })).replace(/=/g, "");
  const secret = "farmlens-dev-secret"; // matches backend JWT_SECRET override
  const key = await crypto.subtle.importKey(
    "raw", new TextEncoder().encode(secret),
    { name: "HMAC", hash: "SHA-256" }, false, ["sign"]
  );
  const sig = await crypto.subtle.sign("HMAC", key, new TextEncoder().encode(`${header}.${payload}`));
  const sigB64 = btoa(String.fromCharCode(...new Uint8Array(sig))).replace(/\+/g, "-").replace(/\//g, "_").replace(/=/g, "");
  return `${header}.${payload}.${sigB64}`;
}

function saveToken(token: string) { localStorage.setItem("farmlens_token", token); }
function clearToken() { localStorage.removeItem("farmlens_token"); }

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(() => {
    const saved = localStorage.getItem("farmlens_user");
    return saved ? JSON.parse(saved) : null;
  });

  const [history, setHistory] = useState<AnalysisRecord[]>(() => {
    const saved = localStorage.getItem("farmlens_history");
    return saved ? JSON.parse(saved) : [];
  });

  const login = useCallback((email: string, _password: string) => {
    const userId = crypto.randomUUID();
    const u: User = { name: email.split("@")[0], email, userId };
    setUser(u);
    localStorage.setItem("farmlens_user", JSON.stringify(u));
    sessionStorage.setItem("farmlens_just_logged_in", "1"); // flag for Result page
    buildJWT(userId, email).then(saveToken);
  }, []);

  const register = useCallback((name: string, email: string, _password: string) => {
    const userId = crypto.randomUUID();
    const u: User = { name, email, userId };
    setUser(u);
    localStorage.setItem("farmlens_user", JSON.stringify(u));
    sessionStorage.setItem("farmlens_just_logged_in", "1"); // flag for Result page
    buildJWT(userId, email).then(saveToken);
  }, []);

  const logout = useCallback(() => {
    setUser(null);
    localStorage.removeItem("farmlens_user");
    clearToken();
  }, []);

  const updateProfile = useCallback((updates: Partial<User & { password?: string }>) => {
    setUser(prev => {
      if (!prev) return prev;
      const { password: _, ...rest } = updates;
      const updated = { ...prev, ...rest };
      localStorage.setItem("farmlens_user", JSON.stringify(updated));
      return updated;
    });
  }, []);

  const addAnalysis = useCallback((record: Omit<AnalysisRecord, "id" | "date">) => {
    const newRecord: AnalysisRecord = {
      ...record,
      id: crypto.randomUUID(),
      date: new Date().toISOString(),
      // Don't store imagePreview in history to avoid quota issues
      imagePreview: undefined,
    };
    setHistory(prev => {
      const updated = [newRecord, ...prev].slice(0, 50); // Keep only last 50 records
      try {
        localStorage.setItem("farmlens_history", JSON.stringify(updated));
      } catch (e) {
        // If quota exceeded, keep only last 20 records
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
    <AuthContext.Provider value={{ user, isAuthenticated: !!user, login, register, logout, updateProfile, history, addAnalysis }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
};
