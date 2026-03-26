import { useState } from "react";
import { useApp } from "../context/AppContext";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select";
import { Badge } from "../components/ui/badge";
import { Plus, Trash2, ChefHat, Minus, Pencil } from "lucide-react";
import type { Recipe, RecipeIngredient } from "../types";
import { toast } from "sonner";
import {
  createRecipe,
  fetchRecipesState,
  deleteRecipeById,
  updateRecipe,
} from "../lib/api";

export function RecipesPage() {
  const { ingredients, recipes, replaceBackendState } = useApp();
  const mainRecipes = recipes.filter((recipe) => recipe.category === "principal");

  const [recipeName, setRecipeName] = useState("");
  const [recipeCategory] = useState<"principal">("principal");
  const [recipeIngredients, setRecipeIngredients] = useState<RecipeIngredient[]>([]);
  const [editingRecipe, setEditingRecipe] = useState<Recipe | null>(null);

  const addIngredientToRecipe = () => {
    setRecipeIngredients([...recipeIngredients, { ingredientId: "", quantity: 1 }]);
  };

  const removeIngredientFromRecipe = (index: number) => {
    setRecipeIngredients(recipeIngredients.filter((_, i) => i !== index));
  };

  const updateRecipeIngredient = (
    index: number,
    field: keyof RecipeIngredient,
    value: string | number
  ) => {
    const updated = [...recipeIngredients];
    updated[index] = { ...updated[index], [field]: value };
    setRecipeIngredients(updated);
  };

  const handleCreateRecipe = async () => {
    if (!recipeName.trim()) {
      toast.error("Veuillez saisir un nom de recette");
      return;
    }

    const validIngredients = recipeIngredients.filter(
      (ing) => ing.ingredientId && ing.quantity > 0
    );

    if (validIngredients.length === 0) {
      toast.error("Veuillez ajouter au moins un ingrédient");
      return;
    }

    try {
      if (editingRecipe) {
        await updateRecipe({
          id: editingRecipe.id,
          name: recipeName,
          ingredients: validIngredients,
        });

        toast.success("Recette modifiée avec succès");
      } else {
        await createRecipe({
          name: recipeName,
          ingredients: validIngredients,
        });

        toast.success(`Recette "${recipeName}" créée`);
      }

      const refreshed = await fetchRecipesState();
      replaceBackendState(
        refreshed.recipes,
        null,
        refreshed.ingredients
      );

      setEditingRecipe(null);
      setRecipeName("");
      setRecipeIngredients([]);
    } catch (error) {
      console.error(error);
      toast.error("Erreur lors de l'enregistrement");
    }
  };

  const getIngredientName = (id: string) => {
    return ingredients.find((ing) => ing.id === id)?.name || "Inconnu";
  };

  const getIngredientUnit = (id: string) => {
    return ingredients.find((ing) => ing.id === id)?.unit || "";
  };

  const getCategoryLabel = (category: string) => {
    const labels: Record<string, string> = {
      principal: "Plat principal",
      accompagnement: "Accompagnement",
    };
    return labels[category] || category;
  };

  const getCategoryColor = (category: string) => {
    const colors: Record<string, "default" | "secondary" | "outline"> = {
      principal: "default",
      accompagnement: "secondary",
      boisson: "outline",
    };
    return colors[category] || "default";
  };

  return (
    <div className="space-y-6 pb-20">
      <Card className="rounded-2xl border-0 shadow-sm">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <ChefHat className="size-5" />
            {editingRecipe ? "Modifier une recette" : "Créer une recette"}
          </CardTitle>
        </CardHeader>

        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="recipe-name" className="text-sm text-muted-foreground">
              Nom de la recette
            </Label>
            <Input
              id="recipe-name"
              placeholder="Ex: Œufs brouillés"
              value={recipeName}
              onChange={(e) => setRecipeName(e.target.value)}
              className="rounded-xl border-gray-200"
            />
          </div>

          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <Label className="text-sm text-muted-foreground">Ingrédients</Label>
              <Button
                size="sm"
                variant="outline"
                onClick={addIngredientToRecipe}
                className="rounded-full"
              >
                <Plus className="size-4 mr-1" />
                Ajouter
              </Button>
            </div>

            {recipeIngredients.length === 0 ? (
              <div className="text-center py-8 text-sm text-muted-foreground bg-muted/30 rounded-xl">
                Aucun ingrédient ajouté
              </div>
            ) : (
              <div className="space-y-2">
                {recipeIngredients.map((recipeIng, index) => (
                  <div key={index} className="flex items-center gap-2">
                    <Select
                      value={recipeIng.ingredientId}
                      onValueChange={(value) =>
                        updateRecipeIngredient(index, "ingredientId", value)
                      }
                    >
                      <SelectTrigger className="flex-1 rounded-xl border-gray-200">
                        <SelectValue placeholder="Sélectionner..." />
                      </SelectTrigger>
                      <SelectContent>
                        {ingredients.map((ing) => (
                          <SelectItem key={ing.id} value={ing.id}>
                            {ing.name} ({ing.unit})
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>

                    <Input
                      type="number"
                      min="0"
                      step="0.1"
                      className="w-24 rounded-xl border-gray-200"
                      value={recipeIng.quantity}
                      onChange={(e) =>
                        updateRecipeIngredient(
                          index,
                          "quantity",
                          parseFloat(e.target.value) || 0
                        )
                      }
                    />

                    <Button
                      size="icon"
                      variant="ghost"
                      onClick={() => removeIngredientFromRecipe(index)}
                      className="rounded-full"
                    >
                      <Minus className="size-4" />
                    </Button>
                  </div>
                ))}
              </div>
            )}
          </div>

          <Button className="w-full rounded-full h-12" onClick={handleCreateRecipe}>
            <Plus className="size-4 mr-2" />
            {editingRecipe ? "Modifier la recette" : "Créer la recette"}
          </Button>

          {editingRecipe && (
            <Button
              variant="outline"
              className="w-full rounded-full"
              onClick={() => {
                setEditingRecipe(null);
                setRecipeName("");
                setRecipeIngredients([]);
              }}
            >
              Annuler la modification
            </Button>
          )}
        </CardContent>
      </Card>

      <div className="space-y-3">
        <h2 className="text-xl font-semibold">Mes recettes ({mainRecipes.length})</h2>

        {mainRecipes.length === 0 ? (
          <Card className="rounded-2xl border-0 shadow-sm">
            <CardContent className="py-12 text-center text-muted-foreground">
              Aucune recette créée
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-3">
            {mainRecipes.map((recipe) => (
              <Card key={recipe.id} className="rounded-2xl border-0 shadow-sm">
                <CardContent className="p-4">
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <h3 className="font-semibold text-lg">{recipe.name}</h3>
                      <Badge
                        variant={getCategoryColor(recipe.category)}
                        className="mt-2 rounded-full"
                      >
                        {getCategoryLabel(recipe.category)}
                      </Badge>
                    </div>

                    <div className="flex items-center gap-2">
                      <Button
                        size="icon"
                        variant="ghost"
                        className="rounded-full"
                        onClick={() => {
                          setEditingRecipe(recipe);
                          setRecipeName(recipe.name);
                          setRecipeIngredients(recipe.ingredients);
                        }}
                      >
                        <Pencil className="size-4" />
                      </Button>

                      <Button
                        size="icon"
                        variant="ghost"
                        className="text-destructive rounded-full"
                        onClick={async () => {
                          try {
                            await deleteRecipeById(recipe.id);

                            const refreshed = await fetchRecipesState();
                            replaceBackendState(
                              refreshed.recipes,
                              null,
                              refreshed.ingredients
                            );

                            toast.success("Recette supprimée");
                          } catch (error) {
                            console.error(error);

                            if (
                              error instanceof Error &&
                              error.message === "recipe_used_in_offer"
                            ) {
                              toast.error("Cette recette est utilisée dans l'offre du jour");
                            } else {
                              toast.error("Erreur lors de la suppression");
                            }
                          }
                        }}
                      >
                        <Trash2 className="size-4" />
                      </Button>
                    </div>
                  </div>

                  <div className="space-y-2 bg-muted/30 rounded-xl p-3">
                    <div className="text-sm font-medium text-muted-foreground">
                      Ingrédients :
                    </div>
                    {recipe.ingredients.map((ing, idx) => (
                      <div key={idx} className="text-sm flex items-center gap-2">
                        <span className="size-1.5 rounded-full bg-primary" />
                        {getIngredientName(ing.ingredientId)} : {ing.quantity}{" "}
                        {getIngredientUnit(ing.ingredientId)}
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}