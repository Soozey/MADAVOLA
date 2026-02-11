import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './contexts/AuthContext'
import { ToastProvider } from './contexts/ToastContext'
import { ProtectedRoute } from './components/ProtectedRoute'
import LoginPage from './pages/LoginPage'
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
import VerifyEntryPage from './pages/VerifyEntryPage'
import ReportsPage from './pages/ReportsPage'
import AuditPage from './pages/AuditPage'
import InspectionsPage from './pages/InspectionsPage'
import ExportsPage from './pages/ExportsPage'
import InvoicesPage from './pages/InvoicesPage'
import LedgerPage from './pages/LedgerPage'
import ViolationsPage from './pages/ViolationsPage'
import PenaltiesPage from './pages/PenaltiesPage'
import Layout from './components/Layout'

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <ToastProvider>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/verify/actor/:id" element={<VerifyActorPage />} />
            <Route
              path="/"
              element={
                <ProtectedRoute>
                  <Layout />
                </ProtectedRoute>
              }
            >
              <Route index element={<Navigate to="/dashboard" replace />} />
              <Route path="dashboard" element={<DashboardPage />} />
              <Route path="dashboard/national" element={<DashboardNationalPage />} />
              <Route path="dashboard/regional" element={<DashboardRegionalPage />} />
              <Route path="dashboard/commune" element={<DashboardCommunePage />} />
              <Route path="actors" element={<ActorsPage />} />
              <Route path="actors/:id" element={<ActorDetailPage />} />
              <Route path="ma-carte" element={<MaCartePage />} />
              <Route path="lots" element={<LotsPage />} />
              <Route path="lots/:id" element={<LotDetailPage />} />
              <Route path="transactions" element={<TransactionsPage />} />
              <Route path="transactions/:id" element={<TransactionDetailPage />} />
              <Route path="exports" element={<ExportsPage />} />
              <Route path="invoices" element={<InvoicesPage />} />
              <Route path="ledger" element={<LedgerPage />} />
              <Route path="reports" element={<ReportsPage />} />
              <Route path="audit" element={<AuditPage />} />
              <Route path="inspections" element={<InspectionsPage />} />
              <Route path="violations" element={<ViolationsPage />} />
              <Route path="penalties" element={<PenaltiesPage />} />
              <Route path="verify" element={<VerifyEntryPage />} />
            </Route>
          </Routes>
        </ToastProvider>
      </AuthProvider>
    </BrowserRouter>
  )
}

export default App