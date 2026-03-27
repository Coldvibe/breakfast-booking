import { useState } from "react";
import { useApp } from "../context/AppContext";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select";
import { Badge } from "../components/ui/badge";
import { Plus, Package, Pencil, Check, X, Trash2 } from "lucide-react";
import type { Ingredient } from "../types";
import { toast } from "sonner";
import { createFood, deleteFood, fetchDailyOfferState, updateFoodSide, updateFoodStock, updateFoodThreshold } from "../lib/api";
import { Switch } from "../components/ui/switch";


export function StocksPage() {
  const { ingredients, replaceBackendState } = useApp();
  const [newIngName, setNewIngName] = useState("");
  const [newIngUnit, setNewIngUnit] = useState("pièce");
  const [newIngStock, setNewIngStock] = useState("0");
  const [editThreshold, setEditThreshold] = useState("");
  const [editingIngredientId, setEditingIngredientId] = useState<string | null>(null);
  const [isEditingIngredient, setIsEditingIngredient] = useState(false);
  const [newIngImageUrl, setNewIngImageUrl] = useState("");

  const handleAddIngredient = async () => {
    if (!newIngName.trim()) {
      toast.error("Veuillez saisir un nom d'ingrédient");
      return;
    }

    try {
      if (isEditingIngredient && editingIngredientId) {
        const numericId = Number(editingIngredientId.replace("f-", ""));

        await updateFoodStock(editingIngredientId, {
          name: newIngName.trim(),
          unit: newIngUnit,
          stock: parseFloat(newIngStock) || 0,
          imageUrl: newIngImageUrl,
        });

        await updateFoodThreshold(numericId, parseFloat(editThreshold) || 0);

        toast.success("Ingrédient modifié");
      } else {
        await createFood({
          name: newIngName,
          unit: newIngUnit,
          stock: parseFloat(newIngStock) || 0,
          imageUrl: newIngImageUrl,
        });

        toast.success(`${newIngName} ajouté au stock`);
      }

      const refreshed = await fetchDailyOfferState();
      replaceBackendState(
        refreshed.recipes,
        refreshed.dailyOffer,
        refreshed.ingredients
      );

      // reset
      setNewIngName("");
      setNewIngUnit("pièce");
      setNewIngStock("0");
      setEditThreshold("");
      setIsEditingIngredient(false);
      setEditingIngredientId(null);
      setNewIngImageUrl("");

    } catch (error) {
      console.error(error);

      if (error instanceof Error && error.message === "duplicate_food") {
        toast.error("Cet ingrédient existe déjà");
      } else {
        toast.error("Erreur lors de l'opération");
      }
    }
  };

  const startEditing = (ingredient: Ingredient) => {
    setIsEditingIngredient(true);
    setEditingIngredientId(ingredient.id);

    setNewIngName(ingredient.name);
    setNewIngUnit(ingredient.unit);
    setNewIngStock(ingredient.stock.toString());
    setEditThreshold(((ingredient as any).lowStockThreshold ?? 0).toString());
    setNewIngImageUrl((ingredient as any).imageUrl ?? "");
  };

  const cancelEditing = () => {
    setIsEditingIngredient(false);
    setEditingIngredientId(null);

    setNewIngName("");
    setNewIngUnit("pièce");
    setNewIngStock("0");
    setEditThreshold("");
    setNewIngImageUrl("");
  };




  const toggleSide = async (ingredient: Ingredient) => {
    try {
      const numericId = Number(ingredient.id.replace("f-", ""));

      await updateFoodSide(numericId, !ingredient.isSide);

      const refreshed = await fetchDailyOfferState();
      replaceBackendState(
        refreshed.recipes,
        refreshed.dailyOffer,
        refreshed.ingredients
      );

      toast.success("Type d’ingrédient mis à jour");
    } catch (error) {
      console.error(error);
      toast.error("Erreur lors de la mise à jour du type d’ingrédient");
    }
  };
    const handleDeleteIngredient = async (ingredient: Ingredient) => {
    const confirmed = window.confirm(
      `Supprimer "${ingredient.name}" du stock ?`
    );

    if (!confirmed) return;

    try {
      const numericId = Number(ingredient.id.replace("f-", ""));

      await deleteFood(numericId);

      const refreshed = await fetchDailyOfferState();
      replaceBackendState(
        refreshed.recipes,
        refreshed.dailyOffer,
        refreshed.ingredients
      );

      toast.success("Ingrédient supprimé");
    } catch (error) {
      console.error(error);

      if (error instanceof Error && error.message === "food_used_in_recipe") {
        toast.error("Impossible : cet ingrédient est utilisé dans une recette");
      } else if (error instanceof Error && error.message === "food_used_in_offer") {
        toast.error("Impossible : cet ingrédient est utilisé dans l’offre du jour");
      } else if (error instanceof Error && error.message === "food_not_found") {
        toast.error("Ingrédient introuvable");
      } else {
        toast.error("Erreur lors de la suppression de l’ingrédient");
      }
    }
  };
  const getStockColor = (ingredient: Ingredient) => {
    const threshold = (ingredient as any).lowStockThreshold ?? 0;

    if (ingredient.stock === 0) return "destructive";
    if (threshold > 0 && ingredient.stock <= threshold) return "destructive";
    if (ingredient.stock < 20) return "secondary";
    return "default";
  };
  const isLowStock = (ingredient: Ingredient) => {
    const threshold = (ingredient as any).lowStockThreshold ?? 0;
    return threshold > 0 && ingredient.stock <= threshold;
  };

  return (
    <div className="space-y-6 pb-20">
      {/* Formulaire d'ajout */}
      <Card className="rounded-2xl border-0 shadow-sm">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Package className="size-5" />
            {isEditingIngredient ? "Modifier l’ingrédient" : "Ajouter un ingrédient"}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="ing-name" className="text-sm text-muted-foreground">Nom de l'ingrédient</Label>
            <Input
              id="ing-name"
              placeholder="Ex: Œuf"
              value={newIngName}
              onChange={(e) => setNewIngName(e.target.value)}
              className="rounded-xl border-gray-200"
              disabled={isEditingIngredient}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="ing-image-url" className="text-sm text-muted-foreground">
              URL de l’image
            </Label>
            <Input
              id="ing-image-url"
              placeholder="https://..."
              value={newIngImageUrl}
              onChange={(e) => setNewIngImageUrl(e.target.value)}
              className="rounded-xl border-gray-200"
            />
          </div>
          {newIngImageUrl && (
            <div className="rounded-2xl overflow-hidden bg-gray-100 border border-gray-200">
              <img
                src={newIngImageUrl}
                alt="Aperçu ingrédient"
                className="w-full h-40 object-cover"
              />
            </div>
          )}
                    <div className="grid grid-cols-3 gap-3">
  
            {/* Unité */}
            <div className="space-y-2">
              <Label htmlFor="ing-unit" className="text-sm text-muted-foreground">
                Unité
              </Label>
              <Select
                value={newIngUnit}
                onValueChange={setNewIngUnit}
                disabled={isEditingIngredient}
              >
                <SelectTrigger id="ing-unit" className="rounded-xl border-gray-200">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="pièce">pièce</SelectItem>
                  <SelectItem value="g">gramme (g)</SelectItem>
                  <SelectItem value="ml">millilitre (ml)</SelectItem>
                  <SelectItem value="pincée">pincée</SelectItem>
                  <SelectItem value="sachet">sachet</SelectItem>
                  <SelectItem value="L">litre (L)</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Stock */}
            <div className="space-y-2">
              <Label htmlFor="ing-stock" className="text-sm text-muted-foreground">
                Stock
              </Label>
              <Input
                id="ing-stock"
                type="number"
                min="0"
                step="0.1"
                value={newIngStock}
                onChange={(e) => setNewIngStock(e.target.value)}
                className="rounded-xl border-gray-200"
              />
            </div>

            {/* Seuil bas (seulement en édition) */}
            <div className="space-y-2">
              <Label htmlFor="ing-threshold" className="text-sm text-muted-foreground">
                Seuil bas
              </Label>
              <Input
                id="ing-threshold"
                type="number"
                min="0"
                step="0.1"
                value={editThreshold}
                onChange={(e) => setEditThreshold(e.target.value)}
                className="rounded-xl border-gray-200"
                disabled={!isEditingIngredient}
              />
            </div>

          </div>

          <Button className="w-full rounded-full h-12" onClick={handleAddIngredient}>
            {isEditingIngredient ? (
              <Check className="size-4 mr-2" />
            ) : (
              <Plus className="size-4 mr-2" />
            )}
            {isEditingIngredient ? "Enregistrer les modifications" : "Ajouter l'ingrédient"}
          </Button>
          {isEditingIngredient && (
            <Button
              type="button"
              variant="outline"
              className="w-full rounded-full h-12"
              onClick={cancelEditing}
            >
              Annuler la modification
            </Button>
          )}
        </CardContent>
      </Card>

      {/* Liste des stocks */}
      <div className="space-y-3">
        <h2 className="text-xl font-semibold">Stock actuel ({ingredients.length})</h2>
        <div className="space-y-2">
          {ingredients.map((ingredient) => (
            <Card key={ingredient.id} className="rounded-2xl border-0 shadow-sm">
              <CardContent className="p-4">
                <div className="flex items-center gap-4">
                  <div className="w-14 h-14 rounded-xl bg-gray-100 overflow-hidden flex-shrink-0">
                    {(ingredient as any).imageUrl ? (
                      <>
                        <img
                          src={(ingredient as any).imageUrl}
                          alt={ingredient.name}
                          className="w-full h-full object-cover"
                          onError={(e) => {
                            e.currentTarget.style.display = "none";
                            const fallback = e.currentTarget.nextElementSibling as HTMLElement | null;
                            if (fallback) {
                              fallback.style.display = "flex";
                            }
                          }}
                        />
                        <div className="w-full h-full items-center justify-center text-xs text-gray-400 hidden">
                          IMG
                        </div>
                      </>
                    ) : (
                      <div className="w-full h-full flex items-center justify-center text-xs text-gray-400">
                        IMG
                      </div>
                    )}
                  </div>
                  <div className="flex-1">
                    <div className="font-semibold text-base">{ingredient.name}</div>
                    <div className="text-sm text-muted-foreground mt-1">Unité: {ingredient.unit}</div>
                      <div className="mt-2 flex items-center gap-3">
                        <div style={{ fontSize: 12, opacity: 0.6 }}>
                          Accompagnement
                        </div>

                        <Switch
                          checked={ingredient.isSide}
                          onCheckedChange={() => toggleSide(ingredient)}
                        />
                      </div>
                      <div className="mt-1">
                        <div className="text-xs text-muted-foreground">
                          Seuil bas : {(ingredient as any).lowStockThreshold ?? 0} {ingredient.unit}
                        </div>
                      </div>
                      {isLowStock(ingredient) && (
                        <div className="mt-2">
                          <Badge variant="destructive" className="rounded-full">
                            Stock bas
                          </Badge>
                        </div>
                      )}
                  </div>
                  <div className="flex items-center gap-3 ml-auto">
                    <Badge variant={getStockColor(ingredient)} className="rounded-full px-3">
                      {ingredient.stock} {ingredient.unit}
                    </Badge>

                    <Button
                      size="icon"
                      variant="ghost"
                      onClick={() => startEditing(ingredient)}
                      className="rounded-full"
                    >
                      <Pencil className="size-4" />
                    </Button>

                    <Button
                      size="icon"
                      variant="ghost"
                      onClick={() => handleDeleteIngredient(ingredient)}
                      className="rounded-full"
                    >
                      <Trash2 className="size-4 text-red-600" />
                    </Button>
                  </div>
                 
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
}