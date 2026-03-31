import { useState, useMemo, useEffect, useRef } from "react";
import { useApp } from "../context/AppContext";
import { Button } from "../components/ui/button";
import { Card, CardContent } from "../components/ui/card";
import { Switch } from "../components/ui/switch";
import { Label } from "../components/ui/label";
import { Badge } from "../components/ui/badge";
import { Plus, Minus } from "lucide-react";
import { ImageWithFallback } from "../components/figma/ImageWithFallback";
import { toast } from "sonner";
import type { SelectedItem } from "../types";
import { Input } from "../components/ui/input";

import { saveDailyOfferState,fetchBreakfastPrice, updateBreakfastPrice } from "../lib/api";

export function DailyOfferPage() {
  const { recipes, ingredients, dailyOffers, replaceBackendState } = useApp();

  const tomorrow = useMemo(() => {
    if (dailyOffers.length > 0 && dailyOffers[0].date) {
      return dailyOffers[0].date;
    }

    const date = new Date();
    date.setDate(date.getDate() + 1);
    return date.toISOString().split("T")[0];
  }, [dailyOffers]);

  const [selectedMainDishes, setSelectedMainDishes] = useState<SelectedItem[]>([]);
  const [selectedAccompaniments, setSelectedAccompaniments] = useState<SelectedItem[]>([]);
  const [isPlanned, setIsPlanned] = useState(true);
  const [isOpen, setIsOpen] = useState(true);
  const isSyncingFromBackend = useRef(false);
  const lastSavedPayloadRef = useRef("");
  const [saveStatus, setSaveStatus] = useState<"idle" | "saving" | "saved" | "error">("idle");
  const [breakfastPrice, setBreakfastPrice] = useState("2.5");
  const [isSavingPrice, setIsSavingPrice] = useState(false);

  const existingOffer = dailyOffers.find((offer) => offer.date === tomorrow);

  const hasConfiguredOffer =
    !!existingOffer &&
    (
      existingOffer.mainDishes.length > 0 ||
      existingOffer.accompaniments.length > 0
    );
  const buildPayload = () => ({
    isPlanned,
    isOpen,
    mainDishes: selectedMainDishes,
    accompaniments: selectedAccompaniments,
  });

  const buildPayloadKey = () => JSON.stringify(buildPayload());
  useEffect(() => {
    isSyncingFromBackend.current = true;

    if (existingOffer) {
      setSelectedMainDishes(existingOffer.mainDishes);
      setSelectedAccompaniments(existingOffer.accompaniments);
      setIsPlanned(existingOffer.isPlanned);
      setIsOpen(existingOffer.isOpen);
    } else {
      setSelectedMainDishes([]);
      setSelectedAccompaniments([]);
      setIsPlanned(true);
      setIsOpen(true);
    }
    lastSavedPayloadRef.current = JSON.stringify({
      isPlanned: existingOffer?.isPlanned ?? true,
      isOpen: existingOffer?.isOpen ?? true,
      mainDishes: existingOffer?.mainDishes ?? [],
      accompaniments: existingOffer?.accompaniments ?? [],
    });
    const timeout = setTimeout(() => {
      isSyncingFromBackend.current = false;
    }, 0);

    return () => clearTimeout(timeout);
  }, [existingOffer]);
  useEffect(() => {
    const loadBreakfastPrice = async () => {
      try {
        const data = await fetchBreakfastPrice();
        setBreakfastPrice(String(data.breakfastPrice ?? 2.5));
      } catch (error) {
        console.error(error);
      }
    };

    loadBreakfastPrice();
  }, [tomorrow]);
  useEffect(() => {
    if (saveStatus !== "saved") return;

    const timeout = setTimeout(() => {
      setSaveStatus("idle");
    }, 1500);

    return () => clearTimeout(timeout);
  }, [saveStatus]);

  useEffect(() => {
    if (isSyncingFromBackend.current) return;
    if (!existingOffer) return;
    const payloadKey = buildPayloadKey();
    if (payloadKey === lastSavedPayloadRef.current) return;
    const timeout = setTimeout(async () => {
      try {
        setSaveStatus("saving");

        const data = await saveDailyOfferState({
          isPlanned,
          isOpen,
          mainDishes: selectedMainDishes,
          accompaniments: selectedAccompaniments,
        });

        replaceBackendState(data.recipes, data.dailyOffer, data.ingredients);
        lastSavedPayloadRef.current = payloadKey;
        setSaveStatus("saved");

        console.log("Autosave toggle OK");
      } catch (error) {
        console.error("Autosave error", error);
        setSaveStatus("error");
      }
    }, 400);

    return () => clearTimeout(timeout);
  }, [isPlanned, isOpen]);

  useEffect(() => {
    if (isSyncingFromBackend.current) return;
    if (!existingOffer) return;
    const payloadKey = buildPayloadKey();
    if (payloadKey === lastSavedPayloadRef.current) return;

    const timeout = setTimeout(async () => {
      try {
        setSaveStatus("saving");

        const data = await saveDailyOfferState({
          isPlanned,
          isOpen,
          mainDishes: selectedMainDishes,
          accompaniments: selectedAccompaniments,
        });

        replaceBackendState(data.recipes, data.dailyOffer, data.ingredients);
        lastSavedPayloadRef.current = payloadKey;
        setSaveStatus("saved");

        console.log("Autosave selection OK");
      } catch (error) {
        console.error("Autosave selection error", error);
        setSaveStatus("error");
      }
    }, 500);

    return () => clearTimeout(timeout);
  }, [selectedMainDishes, selectedAccompaniments]);
const handleSaveBreakfastPrice = async () => {
  const parsedPrice = parseFloat(breakfastPrice);

  if (Number.isNaN(parsedPrice)) {
    toast.error("Prix invalide");
    return;
  }

  if (parsedPrice <= 0) {
    toast.error("Le prix doit être supérieur à 0");
    return;
  }

  try {
    setIsSavingPrice(true);
    const data = await updateBreakfastPrice(parsedPrice);
    setBreakfastPrice(String(data.breakfastPrice));
    toast.success("Prix du petit-déjeuner mis à jour");
  } catch (error) {
    console.error(error);

    if (error instanceof Error && error.message === "missing_breakfast_price") {
      toast.error("Prix manquant");
    } else if (error instanceof Error && error.message === "invalid_breakfast_price") {
      toast.error("Prix invalide");
    } else if (error instanceof Error && error.message === "negative_or_zero_breakfast_price") {
      toast.error("Le prix doit être supérieur à 0");
    } else {
      toast.error("Erreur lors de la mise à jour du prix");
    }
  } finally {
    setIsSavingPrice(false);
  }
};
const mainDishRecipes = recipes.filter((r) => r.category === "principal");
const accompanimentRecipes = ingredients.filter((ingredient) => ingredient.isSide);

  const isItemSelected = (recipeId: string, items: SelectedItem[]) => {
    return items.find((item) => item.recipeId === recipeId);
  };

  const toggleSelection = (
    recipeId: string,
    items: SelectedItem[],
    setItems: React.Dispatch<React.SetStateAction<SelectedItem[]>>
  ) => {
    const existing = items.find((item) => item.recipeId === recipeId);
    if (existing) {
      setItems(items.filter((item) => item.recipeId !== recipeId));
    } else {
      setItems([...items, { recipeId, maxPerPerson: 1 }]);
    }
  };

  const updateMaxPerPerson = (
    recipeId: string,
    maxPerPerson: number,
    items: SelectedItem[],
    setItems: React.Dispatch<React.SetStateAction<SelectedItem[]>>
  ) => {
    setItems(
      items.map((item) =>
        item.recipeId === recipeId ? { ...item, maxPerPerson } : item
      )
    );
  };

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
    const recipe = recipes.find((r) => r.id === recipeId);
    if (recipe) {
      return recipe.name;
    }

    const ingredient = ingredients.find((i) => i.id === recipeId);
    return ingredient?.name || "Inconnu";
  };
  const getRecipeImageUrl = (recipeId: string) => {
    const recipe = recipes.find((r) => r.id === recipeId);
    if (recipe) {
      return (recipe as any)?.imageUrl || "";
    }

    const ingredient = ingredients.find((i) => i.id === recipeId);
    return (ingredient as any)?.imageUrl || "";
  };
  return (
    <div className="space-y-6 pb-24">
      {/* Header avec date */}
      <div className="bg-card rounded-2xl p-5 shadow-sm">
        <div className="text-center mb-4">
          <h2 className="text-2xl font-semibold">{formatDateHeader(tomorrow)}</h2>
        </div>

        {/* Statut déjeuner prévu */}
        <div className="flex items-center justify-between pb-4 border-b">
          <div>
            <Label className="text-base font-semibold">Déjeuner</Label>
            <p className="text-sm text-muted-foreground">
              {isPlanned ? "Déjeuner prévu" : "Déjeuner non prévu"}
            </p>
          </div>
          <div className="flex items-center gap-3">
            <Badge variant={isPlanned ? "default" : "secondary"} className="rounded-full">
              {isPlanned ? "Prévu" : "Pas prévu"}
            </Badge>
            <Switch checked={isPlanned} onCheckedChange={setIsPlanned} />
          </div>
        </div>

        {/* Statut réservations */}
        {isPlanned && (
          <div className="flex items-center justify-between pt-4">
            <div>
              <Label className="text-base font-semibold">Réservations</Label>
              <p className="text-sm text-muted-foreground">
                {isOpen ? "Les réservations sont ouvertes" : "Les réservations sont fermées"}
              </p>
            </div>
            <div className="flex items-center gap-3">
              <Badge variant={isOpen ? "default" : "secondary"} className="rounded-full">
                {isOpen ? "Ouvert" : "Fermé"}
              </Badge>
              <Switch checked={isOpen} onCheckedChange={setIsOpen} />
            </div>
          </div>
        )}
      </div>

      {/* Indicateur d'autosave */}
      {(saveStatus === "saving" || saveStatus === "saved" || saveStatus === "error") && (
        <div className="fixed top-[140px] left-1/2 -translate-x-1/2 z-50">
          <div className="flex items-center gap-2 text-xs text-muted-foreground bg-card border border-border shadow-md px-3 py-1 rounded-full">
            
            {saveStatus === "saving" && (
              <>
                <div className="w-2 h-2 rounded-full bg-blue-500 animate-pulse" />
                <span>Sauvegarde...</span>
              </>
            )}

            {saveStatus === "saved" && (
              <>
                <div className="w-2 h-2 rounded-full bg-green-500" />
                <span>Enregistré</span>
              </>
            )}

            {saveStatus === "error" && (
              <>
                <div className="w-2 h-2 rounded-full bg-red-500" />
                <span>Erreur</span>
              </>
            )}

          </div>
        </div>
      )}

      {/* Contenu seulement si déjeuner prévu */}
      {isPlanned && (
        <>
          {/* Plats principaux */}
          <div className="space-y-4">
            <div className="pt-4 border-t mt-4">
              <div className="rounded-2xl bg-muted/40 border border-border/50 p-4">
                <div className="flex items-start justify-between gap-4 flex-wrap">
                  <div className="flex items-start gap-3 min-w-0 flex-1">
                    <div className="flex items-center justify-center size-10 rounded-xl bg-primary/10 text-primary font-semibold">
                      €
                    </div>

                    <div className="min-w-0">
                      <Label className="text-base font-semibold block">
                        Prix du petit-déjeuner
                      </Label>
                      <p className="text-sm text-muted-foreground mt-1">
                        Prix appliqué aux réservations de demain. Le prix de la veille est repris automatiquement.
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 w-full sm:w-auto">
                    <div className="relative w-full sm:w-32">
                      <Input
                        type="number"
                        min="0.01"
                        step="0.01"
                        value={breakfastPrice}
                        onChange={(e) => setBreakfastPrice(e.target.value)}
                        className="rounded-xl pr-8 text-right font-medium"
                      />
                      <span className="absolute right-3 top-1/2 -translate-y-1/2 text-sm text-muted-foreground">
                        €
                      </span>
                    </div>

                    <Button
                      type="button"
                      className="rounded-full"
                      onClick={handleSaveBreakfastPrice}
                      disabled={isSavingPrice}
                    >
                      {isSavingPrice ? "..." : "Enregistrer"}
                    </Button>
                  </div>
                </div>
              </div>
            </div>
            <h3 className="text-lg font-semibold">Plats principaux</h3>
            {mainDishRecipes.length === 0 ? (
              <Card className="rounded-2xl border-0 shadow-sm">
                <CardContent className="py-8 text-center text-muted-foreground">
                  Aucun plat principal disponible. Créez des recettes d'abord.
                </CardContent>
              </Card>
            ) : (
              <div className="space-y-3">
                {mainDishRecipes.map((recipe) => {
                  const selected = isItemSelected(recipe.id, selectedMainDishes);
                  return (
                    <Card
                      key={recipe.id}
                      className={`rounded-2xl border-0 shadow-sm transition-all ${
                        selected ? "ring-2 ring-primary" : ""
                      }`}
                    >
                      <CardContent className="p-4">
                        <div className="flex items-center gap-4">
                          <div className="size-20 rounded-xl overflow-hidden bg-muted flex-shrink-0">
                            <ImageWithFallback
                              src={getRecipeImageUrl(recipe.id)}
                              alt={recipe.name}
                              className="w-full h-full object-cover"
                            />
                          </div>
                          <div className="flex-1">
                            <h4 className="font-semibold text-base">{recipe.name}</h4>
                            {selected && (
                              <div className="flex items-center gap-2 mt-2">
                                <Button
                                  size="icon"
                                  variant="outline"
                                  className="size-8 rounded-full"
                                  onClick={() =>
                                    updateMaxPerPerson(
                                      recipe.id,
                                      Math.max(1, selected.maxPerPerson - 1),
                                      selectedMainDishes,
                                      setSelectedMainDishes
                                    )
                                  }
                                >
                                  <Minus className="size-3" />
                                </Button>
                                <span className="text-sm font-medium w-16 text-center">
                                  Max {selected.maxPerPerson}/pers
                                </span>
                                <Button
                                  size="icon"
                                  variant="outline"
                                  className="size-8 rounded-full"
                                  onClick={() =>
                                    updateMaxPerPerson(
                                      recipe.id,
                                      selected.maxPerPerson + 1,
                                      selectedMainDishes,
                                      setSelectedMainDishes
                                    )
                                  }
                                >
                                  <Plus className="size-3" />
                                </Button>
                              </div>
                            )}
                          </div>
                          <Button
                            variant={selected ? "default" : "outline"}
                            size="sm"
                            className="rounded-full"
                            onClick={() =>
                              toggleSelection(recipe.id, selectedMainDishes, setSelectedMainDishes)
                            }
                          >
                            {selected ? "Ajouté" : "Ajouter"}
                          </Button>
                        </div>
                      </CardContent>
                    </Card>
                  );
                })}
              </div>
            )}
          </div>

          {/* Accompagnements */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold">Accompagnements</h3>
            {accompanimentRecipes.length === 0 ? (
              <Card className="rounded-2xl border-0 shadow-sm">
                <CardContent className="py-8 text-center text-muted-foreground">
                  Aucun accompagnement disponible
                </CardContent>
              </Card>
            ) : (
              <div className="space-y-3">
                {accompanimentRecipes.map((recipe) => {
                  const selected = isItemSelected(recipe.id, selectedAccompaniments);
                  return (
                    <Card
                      key={recipe.id}
                      className={`rounded-2xl border-0 shadow-sm transition-all ${
                        selected ? "ring-2 ring-primary" : ""
                      }`}
                    >
                      <CardContent className="p-4">
                        <div className="flex items-center gap-4">
                          <div className="size-20 rounded-xl overflow-hidden bg-muted flex-shrink-0">
                            <ImageWithFallback
                              src={getRecipeImageUrl(recipe.id)}
                              alt={recipe.name}
                              className="w-full h-full object-cover"
                            />
                          </div>
                          <div className="flex-1">
                            <h4 className="font-semibold text-base">{recipe.name}</h4>
                            {selected && (
                              <div className="flex items-center gap-2 mt-2">
                                <Button
                                  size="icon"
                                  variant="outline"
                                  className="size-8 rounded-full"
                                  onClick={() =>
                                    updateMaxPerPerson(
                                      recipe.id,
                                      Math.max(1, selected.maxPerPerson - 1),
                                      selectedAccompaniments,
                                      setSelectedAccompaniments
                                    )
                                  }
                                >
                                  <Minus className="size-3" />
                                </Button>
                                <span className="text-sm font-medium w-16 text-center">
                                  Max {selected.maxPerPerson}/pers
                                </span>
                                <Button
                                  size="icon"
                                  variant="outline"
                                  className="size-8 rounded-full"
                                  onClick={() =>
                                    updateMaxPerPerson(
                                      recipe.id,
                                      selected.maxPerPerson + 1,
                                      selectedAccompaniments,
                                      setSelectedAccompaniments
                                    )
                                  }
                                >
                                  <Plus className="size-3" />
                                </Button>
                              </div>
                            )}
                          </div>
                          <Button
                            variant={selected ? "default" : "outline"}
                            size="sm"
                            className="rounded-full"
                            onClick={() =>
                              toggleSelection(recipe.id, selectedAccompaniments, setSelectedAccompaniments)
                            }
                          >
                            {selected ? "Ajouté" : "Ajouter"}
                          </Button>
                        </div>
                      </CardContent>
                    </Card>
                  );
                })}
              </div>
            )}
          </div>
        </>
      )}

      {/* Récapitulatif de l'offre */}
      {hasConfiguredOffer && existingOffer?.isPlanned && (
        <Card className="rounded-2xl border border-border/50 shadow-sm bg-card">
          <CardContent className="p-6">
            <h3 className="font-semibold text-lg mb-4 flex items-center gap-2">
              <Badge variant="secondary" className="rounded-full">Offre du jour</Badge>
              Offre du {formatDateHeader(tomorrow)}
            </h3>

            {existingOffer.mainDishes.length > 0 && (
              <div className="mb-4">
                <h4 className="text-sm font-medium text-muted-foreground mb-2">
                  Plats principaux proposés :
                </h4>
                <div className="space-y-2">
                  {existingOffer.mainDishes.map((item) => (
                    <div
                      key={item.recipeId}
                      className="flex items-center justify-between bg-white rounded-lg px-4 py-2"
                    >
                      <span className="font-medium">{getRecipeName(item.recipeId)}</span>
                      <Badge variant="outline" className="rounded-full">
                        Max {item.maxPerPerson}/pers
                      </Badge>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {existingOffer.accompaniments.length > 0 && (
              <div>
                <h4 className="text-sm font-medium text-muted-foreground mb-2">
                  Accompagnements proposés :
                </h4>
                <div className="space-y-2">
                  {existingOffer.accompaniments.map((item) => (
                    <div
                      key={item.recipeId}
                      className="flex items-center justify-between bg-white rounded-lg px-4 py-2"
                    >
                      <span className="font-medium">{getRecipeName(item.recipeId)}</span>
                      <Badge variant="outline" className="rounded-full">
                        Max {item.maxPerPerson}/pers
                      </Badge>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
