import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './contexts/AuthContext'
import { SessionProvider } from './contexts/SessionContext'
import { ToastProvider } from './contexts/ToastContext'
import { ProtectedRoute } from './components/ProtectedRoute'
import { SessionGuard } from './components/SessionGuard'
import LoginPage from './pages/LoginPage'
import RoleSelectPage from './pages/RoleSelectPage'
import FiliereSelectPage from './pages/FiliereSelectPage'
import HomePage from './pages/HomePage'
import DashboardPage from './pages/DashboardPage'
import DashboardNationalPage from './pages/DashboardNationalPage'
import DashboardRegionalPage from './pages/DashboardRegionalPage'
import DashboardCommunePage from './pages/DashboardCommunePage'
import ActorsPage from './pages/ActorsPage'
import LotsPage from './pages/LotsPage'
import TransactionsPage from './pages/TransactionsPage'
import TransactionDetailPage from './pages/TransactionDetailPage'
import LotDetailPage from './pages/LotDetailPage'
import ActorDetailPage from './pages/ActorDetailPage'
import MaCartePage from './pages/MaCartePage'
import VerifyActorPage from './pages/VerifyActorPage'
import VerifyLotPage from './pages/VerifyLotPage'
import VerifyInvoicePage from './pages/VerifyInvoicePage'
import VerifyEntryPage from './pages/VerifyEntryPage'
import ReportsPage from './pages/ReportsPage'
import AuditPage from './pages/AuditPage'
import InspectionsPage from './pages/InspectionsPage'
import ExportsPage from './pages/ExportsPage'
import InvoicesPage from './pages/InvoicesPage'
import LedgerPage from './pages/LedgerPage'
import ViolationsPage from './pages/ViolationsPage'
import PenaltiesPage from './pages/PenaltiesPage'
import OrCompliancePage from './pages/OrCompliancePage'
import TransportsPage from './pages/TransportsPage'
import TransformationsPage from './pages/TransformationsPage'
import TradesPage from './pages/TradesPage'
import NotificationsPage from './pages/NotificationsPage'
import DocumentsPage from './pages/DocumentsPage'
import OpsCoveragePage from './pages/OpsCoveragePage'
import AdminConfigPage from './pages/AdminConfigPage'
import GeoPointDetailPage from './pages/GeoPointDetailPage'
import FeeDetailPage from './pages/FeeDetailPage'
import GeoMapPage from './pages/GeoMapPage'
import AccountOpsPage from './pages/AccountOpsPage'
import Layout from './components/Layout'

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <SessionProvider>
          <ToastProvider>
            <Routes>
              <Route path="/login" element={<LoginPage />} />
              <Route path="/verify/actor/:id" element={<VerifyActorPage />} />
              <Route path="/verify/lot/:id" element={<VerifyLotPage />} />
              <Route path="/verify/invoice/:ref" element={<VerifyInvoicePage />} />

              <Route path="/welcome" element={<Navigate to="/select-role" replace />} />
              <Route
                path="/select-role"
                element={
                  <ProtectedRoute>
                    <SessionGuard>
                      <RoleSelectPage />
                    </SessionGuard>
                  </ProtectedRoute>
                }
              />
              <Route
                path="/select-filiere"
                element={
                  <ProtectedRoute>
                    <SessionGuard>
                      <FiliereSelectPage />
                    </SessionGuard>
                  </ProtectedRoute>
                }
              />

              <Route
                path="/"
                element={
                  <ProtectedRoute>
                    <SessionGuard>
                      <Layout />
                    </SessionGuard>
                  </ProtectedRoute>
                }
              >
                <Route index element={<Navigate to="/home" replace />} />
                <Route path="home" element={<HomePage />} />
                <Route path="dashboard" element={<DashboardPage />} />
                <Route path="dashboard/national" element={<DashboardNationalPage />} />
                <Route path="dashboard/regional" element={<DashboardRegionalPage />} />
                <Route path="dashboard/commune" element={<DashboardCommunePage />} />
                <Route path="actors" element={<ActorsPage />} />
                <Route path="account-ops" element={<AccountOpsPage />} />
                <Route path="actors/:id" element={<ActorDetailPage />} />
                <Route path="ma-carte" element={<MaCartePage />} />
                <Route path="lots" element={<LotsPage />} />
                <Route path="lots/:id" element={<LotDetailPage />} />
                <Route path="transactions" element={<TransactionsPage />} />
                <Route path="trades" element={<TradesPage />} />
                <Route path="transactions/:id" element={<TransactionDetailPage />} />
                <Route path="exports" element={<ExportsPage />} />
                <Route path="transports" element={<TransportsPage />} />
                <Route path="transformations" element={<TransformationsPage />} />
                <Route path="invoices" element={<InvoicesPage />} />
                <Route path="ledger" element={<LedgerPage />} />
                <Route path="reports" element={<ReportsPage />} />
                <Route path="audit" element={<AuditPage />} />
                <Route path="inspections" element={<InspectionsPage />} />
                <Route path="violations" element={<ViolationsPage />} />
                <Route path="penalties" element={<PenaltiesPage />} />
                <Route path="or-compliance" element={<OrCompliancePage />} />
                <Route path="notifications" element={<NotificationsPage />} />
                <Route path="documents" element={<DocumentsPage />} />
                <Route path="ops-coverage" element={<OpsCoveragePage />} />
                <Route path="admin-config" element={<AdminConfigPage />} />
                <Route path="geo-points/:id" element={<GeoPointDetailPage />} />
                <Route path="fees/:id" element={<FeeDetailPage />} />
                <Route path="map" element={<GeoMapPage />} />
                <Route path="verify" element={<VerifyEntryPage />} />
              </Route>
            </Routes>
          </ToastProvider>
        </SessionProvider>
      </AuthProvider>
    </BrowserRouter>
  )
}

export default App
