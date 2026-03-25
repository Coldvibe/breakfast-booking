import { createContext, useContext, useState, ReactNode } from "react";

interface User {
  id: string;
  name: string;
  email: string;
  role: "admin" | "employee";
}

interface AuthContextType {
  user: User | null;
  login: (email: string, password: string) => boolean;
  logout: () => void;
  isAdmin: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Utilisateurs de démonstration
const DEMO_USERS = [
  {
    id: "1",
    name: "Marie Dupont",
    email: "admin@example.com",
    password: "admin",
    role: "admin" as const,
  },
  {
    id: "2",
    name: "Jean Martin",
    email: "jean@example.com",
    password: "1234",
    role: "employee" as const,
  },
  {
    id: "3",
    name: "Sophie Bernard",
    email: "sophie@example.com",
    password: "1234",
    role: "employee" as const,
  },
];

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>({
    id: "1",
    name: "Marie Dupont",
    email: "admin@example.com",
    role: "admin",
  });

  const login = (email: string, password: string): boolean => {
    const foundUser = DEMO_USERS.find(
      (u) => u.email === email && u.password === password
    );

    if (foundUser) {
      setUser({
        id: foundUser.id,
        name: foundUser.name,
        email: foundUser.email,
        role: foundUser.role,
      });
      return true;
    }
    return false;
  };

  const logout = () => {
    setUser(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        login,
        logout,
        isAdmin: user?.role === "admin",
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
