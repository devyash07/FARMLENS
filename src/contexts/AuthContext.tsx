import React, { createContext, useContext, useState, useCallback } from "react";

interface User {
  name: string;
  email: string;
}

interface AnalysisRecord {
  id: string;
  imageName: string;
  disease: string;
  severity: number;
  confidence: number;
  date: string;
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  login: (email: string, password: string) => void;
  logout: () => void;
  history: AnalysisRecord[];
  addAnalysis: (record: Omit<AnalysisRecord, "id" | "date">) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

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
    const u = { name: email.split("@")[0], email };
    setUser(u);
    localStorage.setItem("farmlens_user", JSON.stringify(u));
  }, []);

  const logout = useCallback(() => {
    setUser(null);
    localStorage.removeItem("farmlens_user");
  }, []);

  const addAnalysis = useCallback((record: Omit<AnalysisRecord, "id" | "date">) => {
    const newRecord: AnalysisRecord = {
      ...record,
      id: crypto.randomUUID(),
      date: new Date().toISOString(),
    };
    setHistory(prev => {
      const updated = [newRecord, ...prev];
      localStorage.setItem("farmlens_history", JSON.stringify(updated));
      return updated;
    });
  }, []);

  return (
    <AuthContext.Provider value={{ user, isAuthenticated: !!user, login, logout, history, addAnalysis }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
};
