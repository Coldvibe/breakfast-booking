import { createBrowserRouter, Navigate } from "react-router";
import { Layout } from "./Layout";
import { DailyOfferPage } from "./pages/DailyOfferPage";
import { RecipesPage } from "./pages/RecipesPage";
import { StocksPage } from "./pages/StocksPage";
import { AgentsPage } from "./pages/AgentsPage";
import { HistoryPage } from "./pages/HistoryPage";
import { StatsPage } from "./pages/StatsPage";
import { SettingsPage } from "./pages/SettingsPage";
import { LoginPage } from "./pages/LoginPage";
import { EmployeeMenuPage } from "./pages/EmployeeMenuPage";

export const router = createBrowserRouter([
  {
    path: "/login",
    Component: LoginPage,
  },
  {
    path: "/employee",
    Component: EmployeeMenuPage,
  },
  {
    path: "/",
    Component: Layout,
    children: [
      { index: true, Component: DailyOfferPage },
      { path: "recipes", Component: RecipesPage },
      { path: "stocks", Component: StocksPage },
      { path: "agents", Component: AgentsPage },
      { path: "history", Component: HistoryPage },
      { path: "stats", Component: StatsPage },
      { path: "settings", Component: SettingsPage },
    ],
  },
]);