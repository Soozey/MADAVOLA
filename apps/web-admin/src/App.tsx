import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { useAuthStore } from "./stores/authStore";
import LoginPage from "./pages/LoginPage";
import DashboardPage from "./pages/DashboardPage";
import ActorsPage from "./pages/ActorsPage";
import LotsPage from "./pages/LotsPage";
import TransactionsPage from "./pages/TransactionsPage";
import RolesPage from "./pages/RolesPage";
import ConfigPage from "./pages/ConfigPage";
import Layout from "./components/Layout";

function PrivateRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuthStore();
  return isAuthenticated ? <>{children}</> : <Navigate to="/login" />;
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route
          path="/"
          element={
            <PrivateRoute>
              <Layout />
            </PrivateRoute>
          }
        >
          <Route index element={<DashboardPage />} />
          <Route path="actors" element={<ActorsPage />} />
          <Route path="lots" element={<LotsPage />} />
          <Route path="transactions" element={<TransactionsPage />} />
          <Route path="roles" element={<RolesPage />} />
          <Route path="config" element={<ConfigPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
