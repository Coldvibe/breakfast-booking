import { useState } from "react";
import { Link } from "react-router";
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetDescription, SheetTrigger } from "./ui/sheet";
import { Button } from "./ui/button";
import { Menu, ChefHat, Package, BarChart3, Settings, Coffee, ChevronRight } from "lucide-react";
import { Separator } from "./ui/separator";

const MENU_ITEMS = [
  { path: "/recipes", icon: ChefHat, label: "Recettes", description: "Gérer les recettes" },
  { path: "/stocks", icon: Package, label: "Stocks", description: "Gérer les stocks" },
  { path: "/stats", icon: BarChart3, label: "Statistiques", description: "Analyses et données" },
  { path: "/settings", icon: Settings, label: "Paramètres", description: "Configuration" },
];

export function HamburgerMenu() {
  const [open, setOpen] = useState(false);

  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger asChild>
        <Button variant="ghost" size="icon" className="rounded-lg">
          <Menu className="size-5" />
        </Button>
      </SheetTrigger>
      <SheetContent side="left" className="w-80">
        <SheetHeader className="mb-6">
          <div className="flex items-center gap-3">
            <div className="flex items-center justify-center size-12 rounded-xl bg-primary/10">
              <Coffee className="size-6 text-primary" />
            </div>
            <div>
              <SheetTitle>Backoffice</SheetTitle>
              <SheetDescription className="text-sm text-muted-foreground">
                Petit Déjeuner
              </SheetDescription>
            </div>
          </div>
        </SheetHeader>

        <div className="space-y-2">
          {MENU_ITEMS.map((item) => {
            const Icon = item.icon;
            return (
              <Link
                key={item.path}
                to={item.path}
                onClick={() => setOpen(false)}
                className="flex items-center justify-between p-4 rounded-xl hover:bg-muted transition-colors group"
              >
                <div className="flex items-center gap-3">
                  <div className="flex items-center justify-center size-10 rounded-lg bg-muted group-hover:bg-background transition-colors">
                    <Icon className="size-5 text-muted-foreground" />
                  </div>
                  <div>
                    <div className="font-semibold">{item.label}</div>
                    <div className="text-sm text-muted-foreground">{item.description}</div>
                  </div>
                </div>
                <ChevronRight className="size-4 text-muted-foreground" />
              </Link>
            );
          })}
        </div>

        <Separator className="my-6" />

        <div className="text-sm text-muted-foreground text-center">
          Version 1.0.0
        </div>
      </SheetContent>
    </Sheet>
  );
}