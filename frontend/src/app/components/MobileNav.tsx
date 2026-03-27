import { Link, useLocation } from "react-router";
import { Calendar, Users, History } from "lucide-react";

const NAV_ITEMS = [
  { path: "/", icon: Calendar, label: "Offre" },
  { path: "/users", icon: Users, label: "Utilisateurs" },
  { path: "/history", icon: History, label: "Historique" },
];

export function MobileNav() {
  const location = useLocation();

  return (
    <nav className="fixed bottom-0 left-0 right-0 bg-card border-t z-50 shadow-lg">
      <div className="grid grid-cols-3 h-20 px-2 max-w-md lg:max-w-2xl mx-auto">
        {NAV_ITEMS.map((item) => {
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
              <Icon className={`${isActive ? "size-6" : "size-5"}`} strokeWidth={isActive ? 2.5 : 2} />
              <span className={`text-xs ${isActive ? "font-semibold" : ""}`}>{item.label}</span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}