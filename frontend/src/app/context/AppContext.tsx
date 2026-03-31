import { createContext, useContext, useState, ReactNode, useEffect } from "react";
import type { Ingredient, Recipe, DailyOffer } from "../types";
import { fetchDailyOfferState, fetchMe } from "../lib/api";

interface AppContextType {
  ingredients: Ingredient[];
  recipes: Recipe[];
  dailyOffers: DailyOffer[];

  isAuthenticated: boolean;
  isLoading: boolean;

  setIsAuthenticated: (value: boolean) => void;
  loadBackendState: () => Promise<void>;

  replaceBackendState: (
    recipes: Recipe[],
    dailyOffer?: DailyOffer | null,
    ingredients?: Ingredient[]
  ) => void;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

export function AppProvider({ children }: { children: ReactNode }) {
  const [ingredients, setIngredients] = useState<Ingredient[]>([]);
  const [recipes, setRecipes] = useState<Recipe[]>([]);
  const [dailyOffers, setDailyOffers] = useState<DailyOffer[]>([]);

  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  // 🔥 LOAD BACKEND STATE
  const loadBackendState = async () => {
    try {
      const data = await fetchDailyOfferState();

      setIngredients(data.ingredients || []);
      setRecipes(data.recipes || []);

      if (data.dailyOffer) {
        setDailyOffers([data.dailyOffer]);
      } else {
        setDailyOffers([]);
      }
    } catch (error) {
      console.error("Erreur chargement backend:", error);
    }
  };

  // 🔐 CHECK SESSION AU DÉMARRAGE
  useEffect(() => {
    async function init() {
      try {
        await fetchMe(); // check cookie session
        setIsAuthenticated(true);
        await loadBackendState();
      } catch {
        setIsAuthenticated(false);
      } finally {
        setIsLoading(false);
      }
    }

    init();
  }, []);

  // 🔁 SYNC BACKEND STATE
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
        isAuthenticated,
        isLoading,
        setIsAuthenticated,
        loadBackendState,
        replaceBackendState,
      }}
    >
      {children}
    </AppContext.Provider>
  );
}

export function useApp() {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error("useApp must be used within AppProvider");
  }
  return context;
}
