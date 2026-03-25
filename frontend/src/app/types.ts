// Types pour l'application
export interface Ingredient {
  id: string;
  name: string;
  unit: string; // "pièce", "g", "ml", "pincée"
  stock: number;
}

export interface RecipeIngredient {
  ingredientId: string;
  quantity: number;
}

export interface Recipe {
  id: string;
  name: string;
  category: "principal" | "accompagnement";
  ingredients: RecipeIngredient[];
  createdAt: Date;
}

export interface SelectedItem {
  recipeId: string;
  maxPerPerson: number;
}

export interface DailyOffer {
  id: string;
  date: string; // Format: YYYY-MM-DD
  mainDishes: SelectedItem[]; // Plats principaux avec max par personne
  accompaniments: SelectedItem[]; // Accompagnements avec max par personne
  isPlanned: boolean; // Déjeuner prévu ou non prévu (grève, week-end, etc.)
  isOpen: boolean; // Réservations ouvertes ou fermées
  createdAt: Date;
}