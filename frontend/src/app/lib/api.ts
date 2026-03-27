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
  imageUrl?: string;
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
    let errorCode = "unknown_error";

    try {
      const data = await response.json();
      errorCode = data.error || errorCode;
    } catch {
      // ignore
    }

    throw new Error(errorCode);
  }

  return response.json();
}
export async function createFood(payload: {
  name: string;
  unit: string;
  stock: number;
}) {
  const response = await fetch("/api/admin/foods", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    let errorCode = "unknown_error";

    try {
      const data = await response.json();
      errorCode = data.error || errorCode;
    } catch {
      // ignore
    }

    throw new Error(errorCode);
  }

  return response.json();
}

export async function updateFoodStock(
  foodId: string,
  payload: { name: string; unit: string; stock: number }
) {
  const numericId = Number(foodId.replace("f-", ""));

  const response = await fetch(`/api/admin/foods/${numericId}`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  const data = await response.json().catch(() => null);

  if (!response.ok) {
    throw new Error(
      data?.error || data?.detail || "Impossible de modifier l’ingrédient."
    );
  }

  return data;
}

export async function updateRecipe(payload: {
  id: string;
  name: string;
  ingredients: { ingredientId: string; quantity: number }[];
  imageUrl?: string;
}) {
  const backendId = payload.id.startsWith("r-")
    ? payload.id.replace("r-", "")
    : payload.id;

  const response = await fetch(`/api/admin/recipes/${backendId}`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      name: payload.name,
      ingredients: payload.ingredients,
      imageUrl: payload.imageUrl || "",
    }),
  });

  if (!response.ok) {
    let errorCode = "unknown_error";

    try {
      const data = await response.json();
      errorCode = data.error || errorCode;
    } catch {}

    throw new Error(errorCode);
  }

  return response.json();
}

export async function fetchRecipesState() {
  const response = await fetch("/api/admin/recipes-state");

  if (!response.ok) {
    throw new Error("Erreur API fetchRecipesState");
  }

  return response.json();
}
export async function updateFoodSide(foodId: number, isSide: boolean) {
  const response = await fetch(`/api/admin/foods/${foodId}/side`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ isSide }),
  });

  const data = await response.json().catch(() => null);

  if (!response.ok) {
    throw new Error(data?.error || data?.detail || "Impossible de modifier le type d’ingrédient.");
  }

  return data;
}
export async function deleteFood(foodId: number) {
  const response = await fetch(`/api/admin/foods/${foodId}`, {
    method: "DELETE",
  });

  const data = await response.json().catch(() => null);

  if (!response.ok) {
    throw new Error(data?.error || data?.detail || "Impossible de supprimer l’ingrédient.");
  }

  return data;
}
export async function updateFoodThreshold(foodId: number, lowStockThreshold: number) {
  const response = await fetch(`/api/admin/foods/${foodId}/threshold`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ lowStockThreshold }),
  });

  const data = await response.json().catch(() => null);

  if (!response.ok) {
    throw new Error(
      data?.error || data?.detail || "Impossible de modifier le seuil bas."
    );
  }

  return data;
}