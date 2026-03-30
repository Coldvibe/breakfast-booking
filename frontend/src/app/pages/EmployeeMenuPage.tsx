import { useState, useEffect, useMemo } from "react";
import { useNavigate } from "react-router";
import { useApp } from "../context/AppContext";
import { useAuth } from "../context/AuthContext";
import { Card, CardContent } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { ImageWithFallback } from "../components/figma/ImageWithFallback";
import { CheckCircle2, Circle, Calendar, AlertCircle } from "lucide-react";
import { toast } from "sonner";
import {
  deleteEmployeeReservation,
  fetchEmployeeReservation,
  saveEmployeeReservation,
} from "../lib/api";

export function EmployeeMenuPage() {
  const { recipes, ingredients, dailyOffers } = useApp();
  const { user, logout, isAuthLoading } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (isAuthLoading) return;

    if (!user) {
      navigate("/login", { replace: true });
      return;
    }

    if (user.role === "admin" || user.role === "gestionnaire") {
      navigate("/", { replace: true });
    }
  }, [user, isAuthLoading, navigate]);

  const tomorrow = useMemo(() => {
    const date = new Date();
    date.setDate(date.getDate() + 1);
    return date.toISOString().split("T")[0];
  }, []);

  const todayOffer = dailyOffers.find((offer) => offer.date === tomorrow);

  const [selectedMainDishes, setSelectedMainDishes] = useState<Record<string, number>>({});
  const [selectedAccompaniments, setSelectedAccompaniments] = useState<Record<string, number>>({});
  const [hasSubmitted, setHasSubmitted] = useState(false);

  useEffect(() => {
    if (isAuthLoading) return;
    if (!user) return;
    if (user.role !== "utilisateur") return;

    const loadExistingReservation = async () => {
      try {
        const data = await fetchEmployeeReservation();

        if (data.reservation) {
          setSelectedMainDishes(data.reservation.mainDishes ?? {});
          setSelectedAccompaniments(data.reservation.accompaniments ?? {});
          setHasSubmitted(true);
        } else {
          setSelectedMainDishes({});
          setSelectedAccompaniments({});
          setHasSubmitted(false);
        }
      } catch (error) {
        console.error(error);
        toast.error("Erreur lors du chargement de votre réservation");
      }
    };

    loadExistingReservation();
  }, [user, tomorrow, isAuthLoading]);

  const formatDateHeader = (dateStr: string) => {
    const date = new Date(dateStr);
    const days = ["Dimanche", "Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi"];
    const dayName = days[date.getDay()];
    const day = String(date.getDate()).padStart(2, "0");
    const month = String(date.getMonth() + 1).padStart(2, "0");
    return `${dayName} ${day}/${month}`;
  };

  const getItemName = (itemId: string) => {
    if (itemId.startsWith("r-")) {
      return recipes.find((r) => r.id === itemId)?.name || "Inconnu";
    }

    if (itemId.startsWith("f-")) {
      return ingredients.find((ing) => ing.id === itemId)?.name || "Inconnu";
    }

    return "Inconnu";
  };

  const getItemMaxPerPerson = (itemId: string) => {
    if (!todayOffer) return 0;

    const item = [...todayOffer.mainDishes, ...todayOffer.accompaniments].find(
      (i) => i.recipeId === itemId
    );

    return item?.maxPerPerson || 0;
  };

  const updateMainDishQuantity = (recipeId: string, nextQty: number) => {
    const max = getItemMaxPerPerson(recipeId);
    const safeQty = Math.max(0, Math.min(nextQty, max));

    if (safeQty === 0) {
      setSelectedMainDishes({});
      return;
    }

    setSelectedMainDishes({
      [recipeId]: safeQty,
    });
  };

  const updateAccompanimentQuantity = (recipeId: string, nextQty: number) => {
    const max = getItemMaxPerPerson(recipeId);
    const safeQty = Math.max(0, Math.min(nextQty, max));

    if (safeQty === 0) {
      const { [recipeId]: _, ...rest } = selectedAccompaniments;
      setSelectedAccompaniments(rest);
      return;
    }

    setSelectedAccompaniments({
      ...selectedAccompaniments,
      [recipeId]: safeQty,
    });
  };
  const handleCancelReservation = async () => {
    try {
      await deleteEmployeeReservation();

      setSelectedMainDishes({});
      setSelectedAccompaniments({});
      setHasSubmitted(false);

      toast.success("Votre réservation a été annulée");
    } catch (error) {
      console.error(error);

      if (error instanceof Error && error.message === "not_authenticated") {
        toast.error("Vous devez être connecté");
        navigate("/login", { replace: true });
      } else if (error instanceof Error && error.message === "forbidden") {
        toast.error("Accès refusé");
      } else {
        toast.error("Erreur lors de l’annulation de votre réservation");
      }
    }
  };
  const handleSubmit = async () => {
    if (!user) return;

    if (Object.keys(selectedMainDishes).length === 0) {
      toast.error("Veuillez sélectionner au moins un plat principal");
      return;
    }

    try {
      await saveEmployeeReservation({
        mainDishes: selectedMainDishes,
        accompaniments: selectedAccompaniments,
      });

      setHasSubmitted(true);
      toast.success("Votre commande a été enregistrée !");
    } catch (error) {
      console.error(error);

      if (error instanceof Error && error.message === "not_authenticated") {
        toast.error("Vous devez être connecté");
        navigate("/login", { replace: true });
      } else if (error instanceof Error && error.message === "forbidden") {
        toast.error("Accès refusé");
      } else if (error instanceof Error && error.message === "reservations_closed") {
        toast.error("Les réservations sont fermées");
      } else if (error instanceof Error && error.message === "event_not_planned") {
        toast.error("Aucun déjeuner n’est prévu");
      } else if (error instanceof Error && error.message === "missing_main_dishes") {
        toast.error("Veuillez sélectionner au moins un plat principal");
      } else if (error instanceof Error && error.message === "invalid_main_dish") {
        toast.error("Plat principal invalide");
      } else if (error instanceof Error && error.message === "main_dish_quantity_exceeded") {
        toast.error("Quantité de plat principal dépassée");
      } else if (error instanceof Error && error.message === "invalid_accompaniment") {
        toast.error("Accompagnement invalide");
      } else if (error instanceof Error && error.message === "accompaniment_quantity_exceeded") {
        toast.error("Quantité d’accompagnement dépassée");
      } else {
        toast.error("Erreur lors de l’enregistrement de votre commande");
      }
    }
  };

  const handleModify = () => {
    setHasSubmitted(false);
  };

  const handleLogout = async () => {
    await logout();
    navigate("/login", { replace: true });
  };

  if (isAuthLoading) {
    return null;
  }

  if (!user) {
    return null;
  }

  if (user.role === "admin" || user.role === "gestionnaire") {
    return null;
  }

  if (!todayOffer || !todayOffer.isPlanned) {
    return (
      <div className="min-h-screen bg-muted/30 flex items-center justify-center p-4">
        <Card className="rounded-2xl border-0 shadow-sm max-w-md w-full">
          <CardContent className="py-12 text-center">
            <AlertCircle className="size-16 mx-auto text-muted-foreground mb-4" />
            <h3 className="text-xl font-semibold mb-2">Pas de déjeuner prévu</h3>
            <p className="text-muted-foreground">
              Aucun déjeuner n&apos;est prévu pour {formatDateHeader(tomorrow)}
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

  const mainDishes = todayOffer.mainDishes
    .map((item) => ({
      ...item,
      recipe: recipes.find((r) => r.id === item.recipeId),
    }))
    .filter((item) => item.recipe);

  const accompaniments = todayOffer.accompaniments
    .map((item) => ({
      ...item,
      ingredient: ingredients.find((ing) => ing.id === item.recipeId),
    }))
    .filter((item) => item.ingredient);

  return (
    <div className="min-h-screen bg-muted/30">
      <div className="max-w-2xl mx-auto">
        <div className="bg-card shadow-sm p-6">
          <div className="flex items-center justify-between mb-2">
            <div>
              <p className="text-sm text-muted-foreground">Bonjour,</p>
              <h1 className="text-2xl font-semibold">{user.name}</h1>
            </div>

            <Button variant="outline" onClick={handleLogout}>
              Déconnexion
            </Button>
          </div>
        </div>

        <div className="p-6 space-y-6 pb-32">
          <Card className="rounded-2xl border-0 shadow-sm bg-gradient-to-br from-primary/10 to-accent">
            <CardContent className="p-6 text-center">
              <Calendar className="size-8 mx-auto text-primary mb-2" />
              <h2 className="text-xl font-semibold">Menu de {formatDateHeader(tomorrow)}</h2>
              <p className="text-sm text-muted-foreground mt-1">
                {hasSubmitted ? "Commande enregistrée ✓" : "Faites votre choix"}
              </p>
            </CardContent>
          </Card>

          <div className="space-y-4">
            <h3 className="text-lg font-semibold">
              Choisissez votre plat principal <span className="text-destructive">*</span>
            </h3>
            <p className="text-sm text-muted-foreground">
              Un seul plat principal peut être choisi, avec la quantité autorisée par personne.
            </p>

            <div className="space-y-3">
              {mainDishes.map(({ recipe, recipeId, maxPerPerson }) => {
                if (!recipe) return null;

                const quantity = selectedMainDishes[recipeId] || 0;
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
                            src={(recipe as any).imageUrl || ""}
                            alt={recipe.name}
                            className="w-full h-full object-cover"
                          />
                        </div>

                        <div className="flex-1">
                          <h4 className="font-semibold text-base">{recipe.name}</h4>
                        </div>

                        {!hasSubmitted ? (
                          <div className="flex items-center gap-2">
                            <Button
                              type="button"
                              size="icon"
                              variant="outline"
                              className="rounded-full"
                              onClick={() => updateMainDishQuantity(recipeId, quantity - 1)}
                              disabled={quantity <= 0}
                            >
                              -
                            </Button>

                            <div className="min-w-[72px] text-center">
                              <div className="text-sm font-medium">{quantity}</div>
                              <div className="text-xs text-muted-foreground">
                                sur {maxPerPerson}
                              </div>
                            </div>

                            <Button
                              type="button"
                              size="icon"
                              variant="outline"
                              className="rounded-full"
                              onClick={() => updateMainDishQuantity(recipeId, quantity + 1)}
                              disabled={quantity >= maxPerPerson}
                            >
                              +
                            </Button>
                          </div>
                        ) : isSelected ? (
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

          {accompaniments.length > 0 && (
            <div className="space-y-4">
              <h3 className="text-lg font-semibold">Accompagnements (optionnel)</h3>

              <div className="space-y-3">
                {accompaniments.map(({ ingredient, recipeId, maxPerPerson }) => {
                  if (!ingredient) return null;

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
                              src={(ingredient as any).imageUrl || ""}
                              alt={ingredient.name}
                              className="w-full h-full object-cover"
                            />
                          </div>

                          <div className="flex-1">
                            <h4 className="font-semibold text-base">{ingredient.name}</h4>
                            <p className="text-sm text-muted-foreground mt-1">
                              Max {maxPerPerson} par personne
                            </p>
                          </div>

                          {!hasSubmitted && (
                            <div className="flex items-center gap-2">
                              <Button
                                type="button"
                                size="icon"
                                variant="outline"
                                className="rounded-full"
                                onClick={() => updateAccompanimentQuantity(recipeId, quantity - 1)}
                                disabled={quantity <= 0}
                              >
                                -
                              </Button>

                              <div className="min-w-[72px] text-center">
                                <div className="text-sm font-medium">{quantity}</div>
                                <div className="text-xs text-muted-foreground">
                                  sur {maxPerPerson}
                                </div>
                              </div>

                              <Button
                                type="button"
                                size="icon"
                                variant="outline"
                                className="rounded-full"
                                onClick={() => updateAccompanimentQuantity(recipeId, quantity + 1)}
                                disabled={quantity >= maxPerPerson}
                              >
                                +
                              </Button>
                            </div>
                          )}

                          {hasSubmitted && (isSelected ? (
                            <CheckCircle2 className="size-6 text-primary" />
                          ) : (
                            <Circle className="size-6 text-muted-foreground" />
                          ))}
                        </div>
                      </CardContent>
                    </Card>
                  );
                })}
              </div>
            </div>
          )}

          {hasSubmitted ? (
            <Card className="rounded-2xl border-0 shadow-sm bg-green-50">
              <CardContent className="p-6 text-center">
                <CheckCircle2 className="size-12 mx-auto text-green-600 mb-3" />
                <h3 className="font-semibold mb-2">Commande enregistrée</h3>
                <p className="text-sm text-muted-foreground mb-4">
                  Votre menu pour {formatDateHeader(tomorrow)} a été enregistré
                </p>

                <div className="space-y-2 text-left bg-white rounded-xl p-4 mb-4">
                  {Object.entries(selectedMainDishes).map(([recipeId, qty]) => (
                    <div key={recipeId} className="flex justify-between">
                      <span className="text-sm text-muted-foreground">
                        {getItemName(recipeId)} :
                      </span>
                      <span className="font-medium">×{qty}</span>
                    </div>
                  ))}

                  {Object.entries(selectedAccompaniments).map(([recipeId, qty]) => (
                    <div key={recipeId} className="flex justify-between">
                      <span className="text-sm text-muted-foreground">
                        {getItemName(recipeId)} :
                      </span>
                      <span className="font-medium">×{qty}</span>
                    </div>
                  ))}
                </div>

                <div className="flex flex-col gap-3 sm:flex-row sm:justify-center">
                  <Button variant="outline" className="rounded-full" onClick={handleModify}>
                    Modifier ma commande
                  </Button>

                  <Button
                    variant="destructive"
                    className="rounded-full"
                    onClick={handleCancelReservation}
                  >
                    Annuler ma réservation
                  </Button>
                </div>
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