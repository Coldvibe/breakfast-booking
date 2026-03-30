import { createContext, useContext, useEffect, useState, ReactNode } from "react";
import { fetchMe } from "../lib/api";

interface User {
  id: string;
  name: string;
  email: string;
  role: "admin" | "gestionnaire" | "utilisateur";
}

interface AuthContextType {
  user: User | null;
  setUser: (user: User | null) => void;
  logout: () => Promise<void>;
  isAdmin: boolean;
  isAuthLoading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);

  const logout = async () => {
    try {
      await fetch("/api/auth/logout", {
        method: "POST",
        credentials: "include",
      });
    } catch (error) {
      console.error("Logout backend error", error);
    } finally {
      setUser(null);
    }
};
  const [isAuthLoading, setIsAuthLoading] = useState(true);

    useEffect(() => {
      const restoreSession = async () => {
        try {
          const data = await fetchMe();
          setUser(data.user);
        } catch {
          setUser(null);
        } finally {
          setIsAuthLoading(false);
        }
      };

      restoreSession();
    }, []);

  return (
    <AuthContext.Provider
      value={{
        user,
        setUser,
        logout,
        isAdmin: user?.role === "admin" || user?.role === "gestionnaire",
        isAuthLoading,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}