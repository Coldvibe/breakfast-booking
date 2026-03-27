import { createContext, useContext, useState, ReactNode } from "react";
import type { Ingredient, Recipe, DailyOffer } from "../types";
import { useEffect } from "react";
import { fetchDailyOfferState } from "../lib/api";

interface AppContextType {
  ingredients: Ingredient[];
  recipes: Recipe[];
  dailyOffers: DailyOffer[];
  addIngredient: (ingredient: Ingredient) => void;
  updateIngredient: (id: string, ingredient: Partial<Ingredient>) => void;
  deleteIngredient: (id: string) => void;
  addRecipe: (recipe: Recipe) => void;
  deleteRecipe: (id: string) => void;
  addDailyOffer: (offer: DailyOffer) => void;
  updateDailyOffer: (id: string, offer: Partial<DailyOffer>) => void;
  deleteDailyOffer: (id: string) => void;
  replaceBackendState: (
    recipes: Recipe[],
    dailyOffer?: DailyOffer | null,
    ingredients?: Ingredient[]
  ) => void;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

// Données initiales
const INITIAL_INGREDIENTS: Ingredient[] = [
  { id: "1", name: "Œuf", unit: "pièce", stock: 50 },
  { id: "2", name: "Sel", unit: "pincée", stock: 100 },
  { id: "3", name: "Poivre", unit: "pincée", stock: 100 },
  { id: "4", name: "Beurre", unit: "g", stock: 500 },
  { id: "5", name: "Farine", unit: "g", stock: 1000 },
  { id: "6", name: "Lait", unit: "ml", stock: 2000 },
  { id: "7", name: "Sucre", unit: "g", stock: 800 },
  { id: "8", name: "Café", unit: "g", stock: 300 },
  { id: "9", name: "Thé", unit: "sachet", stock: 100 },
  { id: "10", name: "Jus d'orange", unit: "ml", stock: 1500 },
];

const INITIAL_RECIPES: Recipe[] = [
  {
    id: "r1",
    name: "Œuf au plat",
    category: "principal",
    ingredients: [{ ingredientId: "1", quantity: 1 }],
    createdAt: new Date(),
  },
  {
    id: "r2",
    name: "Œufs brouillés",
    category: "principal",
    ingredients: [
      { ingredientId: "1", quantity: 2 },
      { ingredientId: "2", quantity: 1 },
      { ingredientId: "3", quantity: 1 },
      { ingredientId: "4", quantity: 10 },
    ],
    createdAt: new Date(),
  },
  {
    id: "r3",
    name: "Pancakes",
    category: "principal",
    ingredients: [
      { ingredientId: "1", quantity: 1 },
      { ingredientId: "5", quantity: 100 },
      { ingredientId: "6", quantity: 150 },
      { ingredientId: "7", quantity: 20 },
    ],
    createdAt: new Date(),
  },
  {
    id: "r4",
    name: "Pain",
    category: "accompagnement",
    ingredients: [{ ingredientId: "5", quantity: 50 }],
    createdAt: new Date(),
  },
  {
    id: "r5",
    name: "Fromage",
    category: "accompagnement",
    ingredients: [{ ingredientId: "4", quantity: 30 }],
    createdAt: new Date(),
  },
  {
    id: "r6",
    name: "Charcuterie",
    category: "accompagnement",
    ingredients: [],
    createdAt: new Date(),
  },
];

export function AppProvider({ children }: { children: ReactNode }) {
  const [ingredients, setIngredients] = useState<Ingredient[]>(INITIAL_INGREDIENTS);
  const [recipes, setRecipes] = useState<Recipe[]>([]);
  const [dailyOffers, setDailyOffers] = useState<DailyOffer[]>([]);

  useEffect(() => {
    async function loadBackendState() {
      try {
        const data = await fetchDailyOfferState();

        console.log("Backend data:", data);

      setIngredients(data.ingredients || []);
      setRecipes(data.recipes || []);

      if (data.dailyOffer) {
        setDailyOffers([data.dailyOffer]);
      } else {
        setDailyOffers([]);
      }
      } catch (error) {
        console.error("Erreur chargement backend:", error);

        // fallback temporaire
        setRecipes(INITIAL_RECIPES);
      }
    }

    loadBackendState();
  }, []);  

  const addIngredient = (ingredient: Ingredient) => {
    setIngredients([...ingredients, ingredient]);
  };

  const updateIngredient = (id: string, updatedData: Partial<Ingredient>) => {
    setIngredients(
      ingredients.map((ing) => (ing.id === id ? { ...ing, ...updatedData } : ing))
    );
  };

  const deleteIngredient = (id: string) => {
    setIngredients(ingredients.filter((ing) => ing.id !== id));
  };

  const addRecipe = (recipe: Recipe) => {
    setRecipes([...recipes, recipe]);
  };

  const deleteRecipe = (id: string) => {
    setRecipes(recipes.filter((recipe) => recipe.id !== id));
  };

  const addDailyOffer = (offer: DailyOffer) => {
    setDailyOffers([...dailyOffers, offer]);
  };

  const updateDailyOffer = (id: string, updatedData: Partial<DailyOffer>) => {
    setDailyOffers(
      dailyOffers.map((offer) => (offer.id === id ? { ...offer, ...updatedData } : offer))
    );
  };

  const deleteDailyOffer = (id: string) => {
    setDailyOffers(dailyOffers.filter((offer) => offer.id !== id));
  };
  const replaceBackendState = (
    recipesFromBackend: Recipe[],
    dailyOfferFromBackend?: DailyOffer | null,
    ingredientsFromBackend?: Ingredient[]
  ) => {
    if (ingredientsFromBackend) {
      setIngredients(ingredientsFromBackend);
    }

    setRecipes(recipesFromBackend || []);

    if (dailyOfferFromBackend !== undefined) {
      if (dailyOfferFromBackend) {
        setDailyOffers([dailyOfferFromBackend]);
      } else {
        setDailyOffers([]);
      }
    }
  };

  return (
    <AppContext.Provider
      value={{
        ingredients,
        recipes,
        dailyOffers,
        addIngredient,
        updateIngredient,
        deleteIngredient,
        addRecipe,
        deleteRecipe,
        addDailyOffer,
        updateDailyOffer,
        deleteDailyOffer,
        replaceBackendState
      }}
    >
      {children}
    </AppContext.Provider>
  );
}

export function useApp() {
  const context = useContext(AppContext);
  if (context === undefined) {
    throw new Error("useApp must be used within an AppProvider");
  }
  return context;
}