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
  imageUrl?: string;
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
  payload: { name: string; unit: string; stock: number; imageUrl?: string }
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
export async function fetchAgentsState() {
  const response = await fetch("/api/admin/agents-state");

  const data = await response.json().catch(() => null);

  if (!response.ok) {
    throw new Error(
      data?.error || data?.detail || "Impossible de charger les agents."
    );
  }

  return data;
}
export async function createAgent(payload: {
  name: string;
  phone: string;
  whatsappOptin?: boolean;
}) {
  const response = await fetch("/api/admin/agents", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  const data = await response.json().catch(() => null);

  if (!response.ok) {
    throw new Error(
      data?.error || data?.detail || "Impossible de créer l’agent."
    );
  }

  return data;
}
export async function updateAgentActive(agentId: string, isActive: boolean) {
  const numericId = Number(agentId.replace("a-", ""));

  const response = await fetch(`/api/admin/agents/${numericId}/active`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ isActive }),
  });

  const data = await response.json().catch(() => null);

  if (!response.ok) {
    throw new Error(
      data?.error || data?.detail || "Impossible de modifier le statut de l’agent."
    );
  }

  return data;
}

export async function fetchUsersState() {
  const response = await fetch("/api/admin/users-state");

  const data = await response.json().catch(() => null);

  if (!response.ok) {
    throw new Error(
      data?.error || data?.detail || "Impossible de charger les utilisateurs."
    );
  }

  return data;
}

export async function createUser(payload: {
  name: string;
  email: string;
  phone?: string;
  password: string;
  role?: "admin" | "gestionnaire" | "utilisateur";
  service?: string;
  imageUrl?: string;
}) {
  const response = await fetch("/api/admin/users", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  const data = await response.json().catch(() => null);

  if (!response.ok) {
    throw new Error(
      data?.error || data?.detail || "Impossible de créer l’utilisateur."
    );
  }

  return data;
}

export async function updateUserActive(userId: string, isActive: boolean) {
  const numericId = Number(userId.replace("u-", ""));

  const response = await fetch(`/api/admin/users/${numericId}/active`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ isActive }),
  });

  const data = await response.json().catch(() => null);

  if (!response.ok) {
    throw new Error(
      data?.error || data?.detail || "Impossible de modifier le statut de l’utilisateur."
    );
  }

  return data;
}

export async function deleteUser(userId: string) {
  const numericId = Number(userId.replace("u-", ""));

  const res = await fetch(`/api/admin/users/${numericId}`, {
    method: "DELETE",
  });

  if (!res.ok) {
    throw new Error("Erreur lors de la suppression de l'utilisateur");
  }

  return await res.json();
}

export async function updateUser(
  userId: string,
  payload: {
    name: string;
    email: string;
    phone?: string;
    role: "admin" | "gestionnaire" | "utilisateur";
    service?: string;
    imageUrl?: string;
  }
) {
  const numericId = Number(userId.replace("u-", ""));

  const response = await fetch(`/api/admin/users/${numericId}`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  const data = await response.json().catch(() => null);

  if (!response.ok) {
    throw new Error(
      data?.error || data?.detail || "Impossible de modifier l’utilisateur."
    );
  }

  return data;
}
export async function loginUser(email: string, password: string) {
  const res = await fetch("/api/auth/login", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    credentials: "include",
    body: JSON.stringify({ email, password }),
  });

  const data = await res.json();

  if (!res.ok) {
    throw new Error(data.error || "login_failed");
  }

  return data;
}
export async function registerUser(payload: {
  name: string;
  email: string;
  password: string;
  phone?: string;
  service?: string;
}) {
  const res = await fetch("/api/auth/register", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  const data = await res.json().catch(() => null);

  if (!res.ok) {
    throw new Error(data?.error || "register_failed");
  }

  return data;
}
export async function fetchMe() {
  const response = await fetch("/api/auth/me", {
    credentials: "include",
  });

  const data = await response.json().catch(() => null);

  if (!response.ok) {
    throw new Error(data?.error || data?.detail || "not_authenticated");
  }

  return data;
}

export async function fetchReservationsState() {
  const response = await fetch("/api/admin/reservations-state", {
    credentials: "include",
  });

  const data = await response.json().catch(() => null);

  if (!response.ok) {
    throw new Error(
      data?.error || data?.detail || "Impossible de charger les réservations."
    );
  }

  return data;
}

export async function fetchEmployeeReservation() {
  const response = await fetch("/api/employee/reservation", {
    credentials: "include",
  });

  const data = await response.json().catch(() => null);

  if (!response.ok) {
    throw new Error(
      data?.error || data?.detail || "Impossible de charger la réservation employé."
    );
  }

  return data;
}

export async function saveEmployeeReservation(payload: {
  mainDishes: Record<string, number>;
  accompaniments: Record<string, number>;
}) {
  const response = await fetch("/api/employee/reservation", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    credentials: "include",
    body: JSON.stringify(payload),
  });

  const data = await response.json().catch(() => null);

  if (!response.ok) {
    throw new Error(
      data?.error || data?.detail || "Impossible d’enregistrer la réservation."
    );
  }

  return data;
}

export async function deleteEmployeeReservation() {
  const response = await fetch("/api/employee/reservation", {
    method: "DELETE",
    credentials: "include",
  });

  const data = await response.json().catch(() => null);

  if (!response.ok) {
    throw new Error(
      data?.error || data?.detail || "Impossible d’annuler la réservation."
    );
  }

  return data;
}

export async function fetchBreakfastPrice() {
  const response = await fetch("/api/admin/breakfast-price", {
    credentials: "include",
  });

  const data = await response.json().catch(() => null);

  if (!response.ok) {
    throw new Error(
      data?.error || data?.detail || "Impossible de charger le prix du petit-déjeuner."
    );
  }

  return data;
}

export async function updateBreakfastPrice(breakfastPrice: number) {
  const response = await fetch("/api/admin/breakfast-price", {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
    },
    credentials: "include",
    body: JSON.stringify({ breakfastPrice }),
  });

  const data = await response.json().catch(() => null);

  if (!response.ok) {
    throw new Error(
      data?.error || data?.detail || "Impossible de mettre à jour le prix du petit-déjeuner."
    );
  }

  return data;
}

export async function fetchEmployeeBreakfastInfo() {
  const response = await fetch("/api/employee/breakfast-info", {
    credentials: "include",
  });

  const data = await response.json().catch(() => null);

  if (!response.ok) {
    throw new Error(
      data?.error || data?.detail || "Impossible de charger les informations du petit-déjeuner."
    );
  }

  return data;
}