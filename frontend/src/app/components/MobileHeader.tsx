import { User, LogOut } from "lucide-react";
import { HamburgerMenu } from "./HamburgerMenu";
import { useAuth } from "../context/AuthContext";
import { Button } from "./ui/button";

interface MobileHeaderProps {
  title: string;
  subtitle?: string;
}

export function MobileHeader({ title, subtitle }: MobileHeaderProps) {
  const { user, logout } = useAuth();

  return (
    <header className="sticky top-0 bg-card z-40 shadow-sm">
      <div className="px-4 py-3">
        <div className="flex items-center justify-between mb-3">
          <HamburgerMenu />
          <Button
            variant="ghost"
            size="icon"
            className="rounded-full"
            onClick={logout}
          >
            <LogOut className="size-4" />
          </Button>
        </div>
        <div>
          <p className="text-sm text-muted-foreground">Bonjour,</p>
          <h1 className="text-2xl font-semibold">{user?.name || "Gestionnaire"}</h1>
        </div>
      </div>
    </header>
  );
}