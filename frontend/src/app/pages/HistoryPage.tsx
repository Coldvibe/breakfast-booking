import { useApp } from "../context/AppContext";
import { Card, CardContent } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import { History, Calendar } from "lucide-react";

export function HistoryPage() {
  const { dailyOffers, recipes } = useApp();

  const formatDateHeader = (dateStr: string) => {
    const date = new Date(dateStr);
    const days = ["Dimanche", "Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi"];
    const dayName = days[date.getDay()];
    const day = String(date.getDate()).padStart(2, "0");
    const month = String(date.getMonth() + 1).padStart(2, "0");
    const year = String(date.getFullYear()).slice(-2);
    return `${dayName} ${day}/${month}/${year}`;
  };

  const getRecipeName = (recipeId: string) => {
    return recipes.find((r) => r.id === recipeId)?.name || "Inconnu";
  };

  const sortedOffers = [...dailyOffers].sort(
    (a, b) => new Date(b.date).getTime() - new Date(a.date).getTime()
  );

  return (
    <div className="space-y-6 pb-24">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2 mb-2">
          <History className="size-6 text-primary" />
          <h2 className="text-2xl font-semibold">Historique</h2>
        </div>
        <p className="text-muted-foreground">Toutes les offres planifiées</p>
      </div>

      {/* Liste des offres */}
      {sortedOffers.length === 0 ? (
        <Card className="rounded-2xl border-0 shadow-sm">
          <CardContent className="py-12 text-center">
            <Calendar className="size-12 mx-auto text-muted-foreground mb-4" />
            <p className="text-muted-foreground">Aucune offre dans l'historique</p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {sortedOffers.map((offer) => {
            const totalItems = offer.mainDishes.length + offer.accompaniments.length;
            return (
              <Card key={offer.id} className="rounded-2xl border-0 shadow-sm">
                <CardContent className="p-5">
                  <div className="flex items-start justify-between mb-4">
                    <div>
                      <h3 className="font-semibold text-lg">{formatDateHeader(offer.date)}</h3>
                      <p className="text-sm text-muted-foreground mt-1">
                        {totalItems} plat(s) au menu
                      </p>
                    </div>
                    <div className="flex flex-col gap-2 items-end">
                      <Badge
                        variant={offer.isPlanned ? "default" : "secondary"}
                        className="rounded-full"
                      >
                        {offer.isPlanned ? "Prévu" : "Pas prévu"}
                      </Badge>
                      {offer.isPlanned && (
                        <Badge
                          variant={offer.isOpen ? "default" : "outline"}
                          className="rounded-full"
                        >
                          {offer.isOpen ? "Ouvert" : "Fermé"}
                        </Badge>
                      )}
                    </div>
                  </div>

                  {offer.isPlanned && (
                    <>
                      {offer.mainDishes.length > 0 && (
                        <div className="mb-3">
                          <div className="text-sm font-medium text-muted-foreground mb-2">
                            Plats principaux :
                          </div>
                          <div className="space-y-1.5">
                            {offer.mainDishes.map((item) => (
                              <div
                                key={item.recipeId}
                                className="flex items-center justify-between bg-muted/30 rounded-lg px-3 py-2"
                              >
                                <span className="text-sm">{getRecipeName(item.recipeId)}</span>
                                <Badge variant="outline" className="rounded-full text-xs">
                                  Max {item.maxPerPerson}/pers
                                </Badge>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {offer.accompaniments.length > 0 && (
                        <div>
                          <div className="text-sm font-medium text-muted-foreground mb-2">
                            Accompagnements :
                          </div>
                          <div className="space-y-1.5">
                            {offer.accompaniments.map((item) => (
                              <div
                                key={item.recipeId}
                                className="flex items-center justify-between bg-muted/30 rounded-lg px-3 py-2"
                              >
                                <span className="text-sm">{getRecipeName(item.recipeId)}</span>
                                <Badge variant="outline" className="rounded-full text-xs">
                                  Max {item.maxPerPerson}/pers
                                </Badge>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </>
                  )}
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
