export async function fetchDailyOfferState() {
  const response = await fetch("/api/admin/daily-offer-state", {
    credentials: "include",
  });

  if (!response.ok) {
    throw new Error("Erreur API");
  }

  return response.json();
}
export async function saveDailyOfferState(payload: any) {
  const response = await fetch("/api/admin/daily-offer-state", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error("Erreur API save");
  }

  return response.json();
}

export async function createRecipe(payload: {
  name: string;
  ingredients: { ingredientId: string; quantity: number }[];
}) {
  const response = await fetch("/api/admin/recipes", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error("Erreur API createRecipe");
  }

  return response.json();
}
export async function deleteRecipeById(recipeId: string) {
  const backendId = recipeId.startsWith("r-")
    ? recipeId.replace("r-", "")
    : recipeId;

  const response = await fetch(`/api/admin/recipes/${backendId}`, {
    method: "DELETE",
  });

  if (!response.ok) {
    throw new Error("Erreur API deleteRecipe");
  }

  return response.json();
}
export async function createFood(payload: {
  name: string;
  unit: string;
}) {
  const response = await fetch("/api/admin/foods", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error("Erreur API createFood");
  }

  return response.json();
}

export async function updateFoodStock(foodId: string, stock: number) {
  const backendId = foodId.startsWith("f-")
    ? foodId.replace("f-", "")
    : foodId;

  const response = await fetch(`/api/admin/foods/${backendId}`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ stock }),
  });

  if (!response.ok) {
    throw new Error("Erreur API updateFoodStock");
  }

  return response.json();
}