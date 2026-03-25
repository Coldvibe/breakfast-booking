import { useState } from "react";
import { useApp } from "../context/AppContext";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select";
import { Badge } from "../components/ui/badge";
import { Plus, Package, Pencil, Check, X } from "lucide-react";
import type { Ingredient } from "../types";
import { toast } from "sonner";
import { createFood, fetchDailyOfferState, updateFoodStock } from "../lib/api";


export function StocksPage() {
  const { ingredients, replaceBackendState } = useApp();
  const [newIngName, setNewIngName] = useState("");
  const [newIngUnit, setNewIngUnit] = useState("pièce");
  const [newIngStock, setNewIngStock] = useState("0");
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editStock, setEditStock] = useState("");

  const handleAddIngredient = async () => {
    if (!newIngName.trim()) {
      toast.error("Veuillez saisir un nom d'ingrédient");
      return;
    }

    try {
      await createFood({
        name: newIngName,
        unit: newIngUnit,
      });

      const refreshed = await fetchDailyOfferState();
      replaceBackendState(refreshed.recipes, refreshed.dailyOffer, refreshed.ingredients);

      toast.success(`${newIngName} ajouté au stock`);

      // Reset form
      setNewIngName("");
      setNewIngUnit("pièce");
      setNewIngStock("0");
    } catch (error) {
      console.error(error);
      toast.error("Erreur lors de l'ajout de l'ingrédient");
    }
  };

  const startEditing = (ingredient: Ingredient) => {
    setEditingId(ingredient.id);
    setEditStock(ingredient.stock.toString());
  };

  const cancelEditing = () => {
    setEditingId(null);
    setEditStock("");
  };

  const saveStock = async (id: string) => {
    const newStock = parseFloat(editStock);

    if (isNaN(newStock) || newStock < 0) {
      toast.error("Stock invalide");
      return;
    }

    try {
      await updateFoodStock(id, newStock);

      const refreshed = await fetchDailyOfferState();
      replaceBackendState(
        refreshed.recipes,
        refreshed.dailyOffer,
        refreshed.ingredients
      );

      toast.success("Stock mis à jour");

      setEditingId(null);
      setEditStock("");
    } catch (error) {
      console.error(error);
      toast.error("Erreur mise à jour du stock");
    }
  };

  const getStockColor = (stock: number) => {
    if (stock === 0) return "destructive";
    if (stock < 20) return "secondary";
    return "default";
  };

  return (
    <div className="space-y-6 pb-20">
      {/* Formulaire d'ajout */}
      <Card className="rounded-2xl border-0 shadow-sm">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Package className="size-5" />
            Ajouter un ingrédient
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
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-2">
              <Label htmlFor="ing-unit" className="text-sm text-muted-foreground">Unité</Label>
              <Select value={newIngUnit} onValueChange={setNewIngUnit}>
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

            <div className="space-y-2">
              <Label htmlFor="ing-stock" className="text-sm text-muted-foreground">Stock initial</Label>
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
          </div>

          <Button className="w-full rounded-full h-12" onClick={handleAddIngredient}>
            <Plus className="size-4 mr-2" />
            Ajouter l'ingrédient
          </Button>
        </CardContent>
      </Card>

      {/* Liste des stocks */}
      <div className="space-y-3">
        <h2 className="text-xl font-semibold">Stock actuel ({ingredients.length})</h2>
        <div className="space-y-2">
          {ingredients.map((ingredient) => (
            <Card key={ingredient.id} className="rounded-2xl border-0 shadow-sm">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="font-semibold text-base">{ingredient.name}</div>
                    <div className="text-sm text-muted-foreground mt-1">Unité: {ingredient.unit}</div>
                  </div>
                  
                  {editingId === ingredient.id ? (
                    <div className="flex items-center gap-2">
                      <Input
                        type="number"
                        min="0"
                        step="0.1"
                        className="w-24 rounded-xl border-gray-200"
                        value={editStock}
                        onChange={(e) => setEditStock(e.target.value)}
                        autoFocus
                      />
                      <Button size="icon" variant="ghost" onClick={() => saveStock(ingredient.id)} className="rounded-full">
                        <Check className="size-4 text-green-600" />
                      </Button>
                      <Button size="icon" variant="ghost" onClick={cancelEditing} className="rounded-full">
                        <X className="size-4" />
                      </Button>
                    </div>
                  ) : (
                    <div className="flex items-center gap-3">
                      <Badge variant={getStockColor(ingredient.stock)} className="rounded-full px-3">
                        {ingredient.stock} {ingredient.unit}
                      </Badge>
                      <Button size="icon" variant="ghost" onClick={() => startEditing(ingredient)} className="rounded-full">
                        <Pencil className="size-4" />
                      </Button>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
}