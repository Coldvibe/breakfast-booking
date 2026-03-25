import { useState, useEffect, useMemo } from "react";
import { useApp } from "../context/AppContext";
import { useAuth } from "../context/AuthContext";
import { Card, CardContent } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { ImageWithFallback } from "../components/figma/ImageWithFallback";
import { getRecipeImage } from "../data/recipeImages";
import { CheckCircle2, Circle, Calendar, AlertCircle } from "lucide-react";
import { toast } from "sonner";

interface EmployeeSelection {
  employeeId: string;
  employeeName: string;
  date: string;
  mainDish: string | null;
  accompaniments: Record<string, number>; // recipeId -> quantity
}

export function EmployeeMenuPage() {
  const { recipes, dailyOffers } = useApp();
  const { user } = useAuth();

  const tomorrow = useMemo(() => {
    const date = new Date();
    date.setDate(date.getDate() + 1);
    return date.toISOString().split("T")[0];
  }, []);

  const todayOffer = dailyOffers.find((offer) => offer.date === tomorrow);

  const [selectedMainDish, setSelectedMainDish] = useState<string | null>(null);
  const [selectedAccompaniments, setSelectedAccompaniments] = useState<Record<string, number>>({});
  const [hasSubmitted, setHasSubmitted] = useState(false);

  // Vérifier si l'employé a déjà fait sa commande (simulation avec localStorage)
  useEffect(() => {
    const saved = localStorage.getItem(`order_${user?.id}_${tomorrow}`);
    if (saved) {
      const data = JSON.parse(saved) as EmployeeSelection;
      setSelectedMainDish(data.mainDish);
      setSelectedAccompaniments(data.accompaniments);
      setHasSubmitted(true);
    }
  }, [user?.id, tomorrow]);

  const formatDateHeader = (dateStr: string) => {
    const date = new Date(dateStr);
    const days = ["Dimanche", "Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi"];
    const dayName = days[date.getDay()];
    const day = String(date.getDate()).padStart(2, "0");
    const month = String(date.getMonth() + 1).padStart(2, "0");
    return `${dayName} ${day}/${month}`;
  };

  const getRecipeName = (recipeId: string) => {
    return recipes.find((r) => r.id === recipeId)?.name || "Inconnu";
  };

  const getRecipeMaxPerPerson = (recipeId: string) => {
    if (!todayOffer) return 0;
    const item = [...todayOffer.mainDishes, ...todayOffer.accompaniments].find(
      (i) => i.recipeId === recipeId
    );
    return item?.maxPerPerson || 0;
  };

  const toggleAccompaniment = (recipeId: string) => {
    const max = getRecipeMaxPerPerson(recipeId);
    const current = selectedAccompaniments[recipeId] || 0;

    if (current === 0) {
      setSelectedAccompaniments({ ...selectedAccompaniments, [recipeId]: 1 });
    } else if (current < max) {
      setSelectedAccompaniments({ ...selectedAccompaniments, [recipeId]: current + 1 });
    } else {
      const { [recipeId]: _, ...rest } = selectedAccompaniments;
      setSelectedAccompaniments(rest);
    }
  };

  const handleSubmit = () => {
    if (!selectedMainDish) {
      toast.error("Veuillez sélectionner un plat principal");
      return;
    }

    const order: EmployeeSelection = {
      employeeId: user!.id,
      employeeName: user!.name,
      date: tomorrow,
      mainDish: selectedMainDish,
      accompaniments: selectedAccompaniments,
    };

    localStorage.setItem(`order_${user?.id}_${tomorrow}`, JSON.stringify(order));
    setHasSubmitted(true);
    toast.success("Votre commande a été enregistrée !");
  };

  const handleModify = () => {
    setHasSubmitted(false);
  };

  if (!todayOffer || !todayOffer.isPlanned) {
    return (
      <div className="min-h-screen bg-muted/30 flex items-center justify-center p-4">
        <Card className="rounded-2xl border-0 shadow-sm max-w-md w-full">
          <CardContent className="py-12 text-center">
            <AlertCircle className="size-16 mx-auto text-muted-foreground mb-4" />
            <h3 className="text-xl font-semibold mb-2">Pas de déjeuner prévu</h3>
            <p className="text-muted-foreground">
              Aucun déjeuner n'est prévu pour {formatDateHeader(tomorrow)}
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!todayOffer.isOpen) {
    return (
      <div className="min-h-screen bg-muted/30 flex items-center justify-center p-4">
        <Card className="rounded-2xl border-0 shadow-sm max-w-md w-full">
          <CardContent className="py-12 text-center">
            <AlertCircle className="size-16 mx-auto text-muted-foreground mb-4" />
            <h3 className="text-xl font-semibold mb-2">Réservations fermées</h3>
            <p className="text-muted-foreground">
              Les réservations pour {formatDateHeader(tomorrow)} sont fermées
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  const mainDishes = todayOffer.mainDishes.map((item) => ({
    ...item,
    recipe: recipes.find((r) => r.id === item.recipeId)!,
  }));

  const accompaniments = todayOffer.accompaniments.map((item) => ({
    ...item,
    recipe: recipes.find((r) => r.id === item.recipeId)!,
  }));

  return (
    <div className="min-h-screen bg-muted/30">
      <div className="max-w-2xl mx-auto">
        {/* Header */}
        <div className="bg-card shadow-sm p-6">
          <div className="flex items-center justify-between mb-2">
            <div>
              <p className="text-sm text-muted-foreground">Bonjour,</p>
              <h1 className="text-2xl font-semibold">{user?.name}</h1>
            </div>
            <Button variant="outline" onClick={() => window.location.href = "/login"}>
              Déconnexion
            </Button>
          </div>
        </div>

        <div className="p-6 space-y-6 pb-32">
          {/* Date */}
          <Card className="rounded-2xl border-0 shadow-sm bg-gradient-to-br from-primary/10 to-accent">
            <CardContent className="p-6 text-center">
              <Calendar className="size-8 mx-auto text-primary mb-2" />
              <h2 className="text-xl font-semibold">Menu de {formatDateHeader(tomorrow)}</h2>
              <p className="text-sm text-muted-foreground mt-1">
                {hasSubmitted ? "Commande enregistrée ✓" : "Faites votre choix"}
              </p>
            </CardContent>
          </Card>

          {/* Plats principaux */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold">
              Choisissez votre plat principal <span className="text-destructive">*</span>
            </h3>
            <div className="space-y-3">
              {mainDishes.map(({ recipe, recipeId }) => {
                const isSelected = selectedMainDish === recipeId;
                return (
                  <Card
                    key={recipeId}
                    className={`rounded-2xl border-0 shadow-sm transition-all cursor-pointer ${
                      isSelected ? "ring-2 ring-primary" : ""
                    } ${hasSubmitted ? "opacity-60 pointer-events-none" : ""}`}
                    onClick={() => !hasSubmitted && setSelectedMainDish(recipeId)}
                  >
                    <CardContent className="p-4">
                      <div className="flex items-center gap-4">
                        <div className="size-20 rounded-xl overflow-hidden bg-muted flex-shrink-0">
                          <ImageWithFallback
                            src={getRecipeImage(recipeId)}
                            alt={recipe.name}
                            className="w-full h-full object-cover"
                          />
                        </div>
                        <div className="flex-1">
                          <h4 className="font-semibold text-base">{recipe.name}</h4>
                        </div>
                        {isSelected ? (
                          <CheckCircle2 className="size-6 text-primary" />
                        ) : (
                          <Circle className="size-6 text-muted-foreground" />
                        )}
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          </div>

          {/* Accompagnements */}
          {accompaniments.length > 0 && (
            <div className="space-y-4">
              <h3 className="text-lg font-semibold">Accompagnements (optionnel)</h3>
              <div className="space-y-3">
                {accompaniments.map(({ recipe, recipeId, maxPerPerson }) => {
                  const quantity = selectedAccompaniments[recipeId] || 0;
                  const isSelected = quantity > 0;
                  return (
                    <Card
                      key={recipeId}
                      className={`rounded-2xl border-0 shadow-sm transition-all ${
                        isSelected ? "ring-2 ring-primary" : ""
                      } ${hasSubmitted ? "opacity-60 pointer-events-none" : ""}`}
                    >
                      <CardContent className="p-4">
                        <div className="flex items-center gap-4">
                          <div className="size-20 rounded-xl overflow-hidden bg-muted flex-shrink-0">
                            <ImageWithFallback
                              src={getRecipeImage(recipeId)}
                              alt={recipe.name}
                              className="w-full h-full object-cover"
                            />
                          </div>
                          <div className="flex-1">
                            <h4 className="font-semibold text-base">{recipe.name}</h4>
                            <p className="text-sm text-muted-foreground mt-1">
                              Max {maxPerPerson} par personne
                            </p>
                            {isSelected && (
                              <Badge className="rounded-full mt-2">
                                Quantité : {quantity}
                              </Badge>
                            )}
                          </div>
                          {!hasSubmitted && (
                            <Button
                              variant={isSelected ? "default" : "outline"}
                              size="sm"
                              className="rounded-full"
                              onClick={() => toggleAccompaniment(recipeId)}
                            >
                              {quantity === 0
                                ? "Ajouter"
                                : quantity < maxPerPerson
                                ? `+1 (${quantity})`
                                : "Retirer"}
                            </Button>
                          )}
                        </div>
                      </CardContent>
                    </Card>
                  );
                })}
              </div>
            </div>
          )}

          {/* Boutons d'action */}
          {hasSubmitted ? (
            <Card className="rounded-2xl border-0 shadow-sm bg-green-50">
              <CardContent className="p-6 text-center">
                <CheckCircle2 className="size-12 mx-auto text-green-600 mb-3" />
                <h3 className="font-semibold mb-2">Commande enregistrée</h3>
                <p className="text-sm text-muted-foreground mb-4">
                  Votre menu pour {formatDateHeader(tomorrow)} a été enregistré
                </p>
                <div className="space-y-2 text-left bg-white rounded-xl p-4 mb-4">
                  <div className="flex justify-between">
                    <span className="text-sm text-muted-foreground">Plat principal :</span>
                    <span className="font-medium">{getRecipeName(selectedMainDish!)}</span>
                  </div>
                  {Object.entries(selectedAccompaniments).map(([recipeId, qty]) => (
                    <div key={recipeId} className="flex justify-between">
                      <span className="text-sm text-muted-foreground">
                        {getRecipeName(recipeId)} :
                      </span>
                      <span className="font-medium">×{qty}</span>
                    </div>
                  ))}
                </div>
                <Button variant="outline" className="rounded-full" onClick={handleModify}>
                  Modifier ma commande
                </Button>
              </CardContent>
            </Card>
          ) : (
            <Button className="w-full rounded-full h-14" size="lg" onClick={handleSubmit}>
              Valider ma commande
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}
