import { Outlet, useLocation, Navigate } from "react-router";
import { MobileNav } from "./components/MobileNav";
import { MobileHeader } from "./components/MobileHeader";
import { Toaster } from "./components/ui/sonner";
import { useAuth } from "./context/AuthContext";
import { useEffect } from "react";
import { useNavigate } from "react-router";

const PAGE_TITLES: Record<string, { title: string; subtitle: string }> = {
  "/": { title: "Offre du jour", subtitle: "Composez le menu de demain" },
  "/recipes": { title: "Recettes", subtitle: "Gérez vos recettes" },
  "/stocks": { title: "Stocks", subtitle: "Gérez vos ingrédients" },
  "/agents": { title: "Agents", subtitle: "Gérez les utilisateurs" },
  "/history": { title: "Historique", subtitle: "Offres passées" },
  "/stats": { title: "Statistiques", subtitle: "Analyses et données" },
  "/settings": { title: "Paramètres", subtitle: "Configuration" },
};

export function Layout() {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, isAdmin } = useAuth();
  const pageInfo = PAGE_TITLES[location.pathname] || { title: "Petit Déjeuner", subtitle: "" };

  useEffect(() => {
    if (!user) {
      navigate("/login");
    } else if (!isAdmin) {
      navigate("/employee");
    }
  }, [user, isAdmin, navigate]);

  if (!user || !isAdmin) {
    return null;
  }

  return (
    <div className="min-h-screen bg-muted/30 flex justify-center">
      {/* Container mobile - responsive */}
      <div className="w-full max-w-md lg:max-w-2xl bg-background min-h-screen shadow-xl relative">
        <MobileHeader title={pageInfo.title} subtitle={pageInfo.subtitle} />
        <main className="px-4 py-6">
          <Outlet />
        </main>
        <MobileNav />
      </div>
      <Toaster />
    </div>
  );
}