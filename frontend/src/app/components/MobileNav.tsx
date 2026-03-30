import { Link, useLocation } from "react-router";
import { Calendar, Users, ClipboardList, Settings } from "lucide-react";
import { useAuth } from "../context/AuthContext";

const ADMIN_NAV_ITEMS = [
  { path: "/", icon: Calendar, label: "Offre" },
  { path: "/reservations", icon: ClipboardList, label: "Réservations" },
  { path: "/users", icon: Users, label: "Utilisateurs" },
];

const USER_NAV_ITEMS = [
  { path: "/employee", icon: Calendar, label: "Réserver" },
  { path: "/settings", icon: Settings, label: "Paramètres" },
];

export function MobileNav() {
  const location = useLocation();
  const { user } = useAuth();

  const isAdminLike =
    user?.role === "admin" || user?.role === "gestionnaire";

  const navItems = isAdminLike ? ADMIN_NAV_ITEMS : USER_NAV_ITEMS;
  const gridColsClass = navItems.length === 3 ? "grid-cols-3" : "grid-cols-2";

  return (
    <nav className="fixed bottom-0 left-0 right-0 bg-card border-t z-50 shadow-lg">
      <div className={`grid ${gridColsClass} h-20 px-2 max-w-md lg:max-w-2xl mx-auto`}>
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = location.pathname === item.path;

          return (
            <Link
              key={item.path}
              to={item.path}
              className={`flex flex-col items-center justify-center gap-1.5 transition-all rounded-xl mx-1 ${
                isActive
                  ? "text-primary bg-accent"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              <Icon
                className={`${isActive ? "size-6" : "size-5"}`}
                strokeWidth={isActive ? 2.5 : 2}
              />
              <span className={`text-xs ${isActive ? "font-semibold" : ""}`}>
                {item.label}
              </span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}