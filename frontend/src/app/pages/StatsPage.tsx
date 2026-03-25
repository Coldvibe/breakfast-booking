import { useApp } from "../context/AppContext";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import { BarChart3, TrendingUp, Package, Calendar } from "lucide-react";

export function StatsPage() {
  const { dailyOffers, recipes, ingredients } = useApp();

  // Statistiques de base
  const totalOffers = dailyOffers.length;
  const plannedOffers = dailyOffers.filter((o) => o.isPlanned).length;
  const openOffers = dailyOffers.filter((o) => o.isOpen).length;

  // Recettes les plus utilisées
  const recipeUsage: Record<string, number> = {};
  dailyOffers.forEach((offer) => {
    offer.mainDishes.forEach((dish) => {
      recipeUsage[dish.recipeId] = (recipeUsage[dish.recipeId] || 0) + 1;
    });
    offer.accompaniments.forEach((acc) => {
      recipeUsage[acc.recipeId] = (recipeUsage[acc.recipeId] || 0) + 1;
    });
  });

  const topRecipes = Object.entries(recipeUsage)
    .sort(([, a], [, b]) => b - a)
    .slice(0, 5)
    .map(([recipeId, count]) => ({
      recipe: recipes.find((r) => r.id === recipeId),
      count,
    }));

  // Stock faible
  const lowStockItems = ingredients.filter((ing) => ing.stock < 20);

  return (
    <div className="space-y-6 pb-24">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2 mb-2">
          <BarChart3 className="size-6 text-primary" />
          <h2 className="text-2xl font-semibold">Statistiques</h2>
        </div>
        <p className="text-muted-foreground">Vue d'ensemble de votre activité</p>
      </div>

      {/* Cartes de statistiques */}
      <div className="grid grid-cols-2 gap-4">
        <Card className="rounded-2xl border-0 shadow-sm">
          <CardContent className="p-5">
            <div className="flex items-center gap-2 mb-2">
              <Calendar className="size-4 text-muted-foreground" />
              <span className="text-sm text-muted-foreground">Total offres</span>
            </div>
            <div className="text-3xl font-bold">{totalOffers}</div>
          </CardContent>
        </Card>

        <Card className="rounded-2xl border-0 shadow-sm">
          <CardContent className="p-5">
            <div className="flex items-center gap-2 mb-2">
              <TrendingUp className="size-4 text-muted-foreground" />
              <span className="text-sm text-muted-foreground">Prévues</span>
            </div>
            <div className="text-3xl font-bold">{plannedOffers}</div>
          </CardContent>
        </Card>

        <Card className="rounded-2xl border-0 shadow-sm">
          <CardContent className="p-5">
            <div className="flex items-center gap-2 mb-2">
              <Package className="size-4 text-muted-foreground" />
              <span className="text-sm text-muted-foreground">Ouvertes</span>
            </div>
            <div className="text-3xl font-bold">{openOffers}</div>
          </CardContent>
        </Card>

        <Card className="rounded-2xl border-0 shadow-sm">
          <CardContent className="p-5">
            <div className="flex items-center gap-2 mb-2">
              <Package className="size-4 text-muted-foreground" />
              <span className="text-sm text-muted-foreground">Recettes</span>
            </div>
            <div className="text-3xl font-bold">{recipes.length}</div>
          </CardContent>
        </Card>
      </div>

      {/* Recettes populaires */}
      <Card className="rounded-2xl border-0 shadow-sm">
        <CardHeader>
          <CardTitle>Recettes les plus utilisées</CardTitle>
        </CardHeader>
        <CardContent>
          {topRecipes.length === 0 ? (
            <p className="text-center text-muted-foreground py-8">
              Aucune donnée disponible
            </p>
          ) : (
            <div className="space-y-3">
              {topRecipes.map(({ recipe, count }, index) => (
                <div
                  key={recipe?.id}
                  className="flex items-center justify-between p-3 rounded-xl bg-muted/30"
                >
                  <div className="flex items-center gap-3">
                    <Badge className="rounded-full size-8 flex items-center justify-center">
                      {index + 1}
                    </Badge>
                    <span className="font-medium">{recipe?.name || "Inconnu"}</span>
                  </div>
                  <Badge variant="outline" className="rounded-full">
                    {count} fois
                  </Badge>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Alertes stock faible */}
      {lowStockItems.length > 0 && (
        <Card className="rounded-2xl border-0 shadow-sm border-l-4 border-l-destructive">
          <CardHeader>
            <CardTitle className="text-destructive">Alertes Stock Faible</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {lowStockItems.map((item) => (
                <div
                  key={item.id}
                  className="flex items-center justify-between p-3 rounded-xl bg-destructive/5"
                >
                  <span className="font-medium">{item.name}</span>
                  <Badge variant="destructive" className="rounded-full">
                    {item.stock} {item.unit}
                  </Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
