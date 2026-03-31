import { createBrowserRouter } from "react-router";
import { Layout } from "./Layout";
import { DailyOfferPage } from "./pages/DailyOfferPage";
import { RecipesPage } from "./pages/RecipesPage";
import { StocksPage } from "./pages/StocksPage";
import { HistoryPage } from "./pages/HistoryPage";
import { StatsPage } from "./pages/StatsPage";
import { SettingsPage } from "./pages/SettingsPage";
import { LoginPage } from "./pages/LoginPage";
import { RegisterPage } from "./pages/RegisterPage";
import { EmployeeMenuPage } from "./pages/EmployeeMenuPage";
import { UsersPage } from "./pages/UsersPage";
import { ReservationsPage } from "./pages/ReservationsPage";
import { CashPage } from "./pages/CashPage";

export const router = createBrowserRouter([
  {
    path: "/login",
    Component: LoginPage,
  },
  {
    path: "/register",
    Component: RegisterPage,
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
      { path: "history", Component: HistoryPage },
      { path: "stats", Component: StatsPage },
      { path: "settings", Component: SettingsPage },
      { path: "users", Component: UsersPage },
      { path: "reservations", Component: ReservationsPage },
      { path: "cash", Component: CashPage },
    ],
  },
]);