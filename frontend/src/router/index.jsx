import { Routes, Route, Navigate } from "react-router-dom";
import { ProtectedRoute } from "./ProtectedRoute";
import AppLayout from "@/components/layout/AppLayout";
import LoginPage from "@/pages/auth/LoginPage";
import DashboardPage from "@/pages/dashboard/DashboardPage";
// Inventaris
import ComponentListPage from "@/pages/inventory/ComponentListPage";
import ComponentDetailPage from "@/pages/inventory/ComponentDetailPage";
// Petugas & Peminjam
import OfficerListPage from "@/pages/officers/OfficerListPage";
import BorrowerListPage from "@/pages/borrowers/BorrowerListPage";
import TransactionListPage from "@/pages/borrow/TransactionListPage";
import TransactionDetailPage from "@/pages/borrow/TransactionDetailPage";
import TransactionFormPage from "@/pages/borrow/TransactionFormPage";
// Pengembalian
import ReturnListPage from "@/pages/returns/ReturnListPage";
import ReturnDetailPage from "@/pages/returns/ReturnDetailPage";
import ReturnFormPage from "@/pages/returns/ReturnFormPage";
// Maintenance
import MaintenanceListPage from "@/pages/maintenance/MaintenanceListPage";
// Admin
import UserListPage from "@/pages/users/UserListPage";
import ActivityLogListPage from "@/pages/activity-logs/ActivityLogListPage";

export default function AppRouter() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />

      {/* Semua role — public read */}
      <Route element={<ProtectedRoute><AppLayout /></ProtectedRoute>}>
        <Route index element={<DashboardPage />} />

        <Route path="inventory/components" element={<ComponentListPage />} />
        <Route path="inventory/components/:id" element={<ComponentDetailPage />} />

        <Route path="officers" element={<OfficerListPage />} />
        <Route path="borrowers" element={<BorrowerListPage />} />

        <Route path="borrow/transactions" element={<TransactionListPage />} />
        <Route path="borrow/transactions/:id" element={<TransactionDetailPage />} />

        <Route path="returns" element={<ReturnListPage />} />
        <Route path="returns/:id" element={<ReturnDetailPage />} />

        <Route path="maintenance" element={<MaintenanceListPage />} />
      </Route>

      {/* Form routes — perlu login */}
      <Route element={<ProtectedRoute requireAuth><AppLayout /></ProtectedRoute>}>
        <Route path="borrow/transactions/new" element={<TransactionFormPage />} />
        <Route path="returns/new" element={<ReturnFormPage />} />
      </Route>

      {/* Admin only */}
      {/* === COMMENT ===
      <Route element={<ProtectedRoute adminOnly><AppLayout /></ProtectedRoute>}>
        <Route path="users" element={<UserListPage />} />
        <Route path="activity-logs" element={<ActivityLogListPage />} />
      </Route>
      */}

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
