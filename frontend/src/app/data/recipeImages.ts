// Images pour les recettes
export const RECIPE_IMAGES: Record<string, string> = {
  "r1": "https://images.unsplash.com/photo-1589786741892-824d46e61d61?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&w=400",
  "r2": "https://images.unsplash.com/photo-1600028657385-f5f772e618b1?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&w=400",
  "r3": "https://images.unsplash.com/photo-1668507740203-0654d38b6201?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&w=400",
  "r4": "https://images.unsplash.com/photo-1645771321012-919d2e7aa858?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&w=400",
  "r5": "https://images.unsplash.com/photo-1606704826978-184395f73727?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&w=400",
};

export const getRecipeImage = (recipeId: string): string => {
  return RECIPE_IMAGES[recipeId] || "https://images.unsplash.com/photo-1533089860892-a7c6f0a88666?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&w=400";
};
