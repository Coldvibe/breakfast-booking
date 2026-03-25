import { useState, useMemo, useEffect } from "react";
import { useApp } from "../context/AppContext";
import { Button } from "../components/ui/button";
import { Card, CardContent } from "../components/ui/card";
import { Switch } from "../components/ui/switch";
import { Label } from "../components/ui/label";
import { Badge } from "../components/ui/badge";
import { Save, Plus, Minus } from "lucide-react";
import { ImageWithFallback } from "../components/figma/ImageWithFallback";
import type { DailyOffer, SelectedItem } from "../types";
import { toast } from "sonner";
import { getRecipeImage } from "../data/recipeImages";

export function DailyOfferPage() {
  const { recipes, dailyOffers, addDailyOffer, updateDailyOffer } = useApp();
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

  const existingOffer = dailyOffers.find((offer) => offer.date === tomorrow);

  // Charger l'offre existante si elle existe
  useEffect(() => {
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
  }, [existingOffer]);

  const mainDishRecipes = recipes.filter((r) => r.category === "principal");
  const accompanimentRecipes = recipes.filter((r) => r.category === "accompagnement");

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

  const handleSaveOffer = () => {
    if (!isPlanned) {
      // Si pas prévu, on peut sauvegarder même sans plats
      if (existingOffer) {
        updateDailyOffer(existingOffer.id, {
          mainDishes: [],
          accompaniments: [],
          isPlanned: false,
          isOpen: false,
        });
        toast.success("Offre mise à jour - Déjeuner non prévu");
      } else {
        const newOffer: DailyOffer = {
          id: `offer${Date.now()}`,
          date: tomorrow,
          mainDishes: [],
          accompaniments: [],
          isPlanned: false,
          isOpen: false,
          createdAt: new Date(),
        };
        addDailyOffer(newOffer);
        toast.success("Offre créée - Déjeuner non prévu");
      }
      return;
    }

    // Vérifier qu'au moins un plat principal est sélectionné
    if (selectedMainDishes.length === 0) {
      toast.error("Veuillez sélectionner au moins un plat principal");
      return;
    }

    if (existingOffer) {
      updateDailyOffer(existingOffer.id, {
        mainDishes: selectedMainDishes,
        accompaniments: selectedAccompaniments,
        isPlanned,
        isOpen,
      });
      toast.success("Offre mise à jour");
    } else {
      const newOffer: DailyOffer = {
        id: `offer${Date.now()}`,
        date: tomorrow,
        mainDishes: selectedMainDishes,
        accompaniments: selectedAccompaniments,
        isPlanned,
        isOpen,
        createdAt: new Date(),
      };
      addDailyOffer(newOffer);
      toast.success("Offre créée");
    }
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
    return recipes.find((r) => r.id === recipeId)?.name || "Inconnu";
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

        {/* Statut réservations (seulement si prévu) */}
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

      {/* Contenu seulement si déjeuner prévu */}
      {isPlanned && (
        <>
          {/* Plats principaux */}
          <div className="space-y-4">
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
                              src={getRecipeImage(recipe.id)}
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
                              src={getRecipeImage(recipe.id)}
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

      {/* Bouton de sauvegarde */}
      <Button className="w-full rounded-full h-14" size="lg" onClick={handleSaveOffer}>
        <Save className="size-5 mr-2" />
        {existingOffer ? "Mettre à jour l'offre" : "Créer l'offre"}
      </Button>

      {/* Récapitulatif de l'offre validée */}
      {existingOffer && existingOffer.isPlanned && (
        <Card className="rounded-2xl border-0 shadow-sm bg-gradient-to-br from-green-50 to-green-100 border-l-4 border-l-green-500">
          <CardContent className="p-6">
            <h3 className="font-semibold text-lg mb-4 flex items-center gap-2">
              <Badge className="rounded-full bg-green-600">Validé</Badge>
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