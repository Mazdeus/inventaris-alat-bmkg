import { Routes, Route, Navigate } from "react-router-dom";
import { ProtectedRoute } from "./ProtectedRoute";
import AppLayout from "@/components/layout/AppLayout";
import LoginPage from "@/pages/auth/LoginPage";
import DashboardPage from "@/pages/dashboard/DashboardPage";
// Inventaris
import ComponentListPage from "@/pages/inventory/ComponentListPage";
import ComponentDetailPage from "@/pages/inventory/ComponentDetailPage";
import ItemListPage from "@/pages/inventory/ItemListPage";
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
// Pelimpahan
import HandoverListPage from "@/pages/handovers/HandoverListPage";
import HandoverDetailPage from "@/pages/handovers/HandoverDetailPage";
import HandoverFormPage from "@/pages/handovers/HandoverFormPage";
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
        <Route path="inventory/items" element={<ItemListPage />} />

        <Route path="officers" element={<OfficerListPage />} />
        <Route path="borrowers" element={<BorrowerListPage />} />

        <Route path="borrow/transactions" element={<TransactionListPage />} />
        <Route path="borrow/transactions/:id" element={<TransactionDetailPage />} />

        <Route path="returns" element={<ReturnListPage />} />
        <Route path="returns/:id" element={<ReturnDetailPage />} />

        <Route path="maintenance" element={<MaintenanceListPage />} />

        <Route path="handovers" element={<HandoverListPage />} />
        <Route path="handovers/:id" element={<HandoverDetailPage />} />
      </Route>

      {/* Form routes — perlu login */}
      <Route element={<ProtectedRoute requireAuth><AppLayout /></ProtectedRoute>}>
        <Route path="borrow/transactions/new" element={<TransactionFormPage />} />
        <Route path="returns/new" element={<ReturnFormPage />} />
      </Route>

      {/* Admin only */}
      <Route element={<ProtectedRoute adminOnly><AppLayout /></ProtectedRoute>}>
        <Route path="users" element={<UserListPage />} />
        <Route path="handovers/new" element={<HandoverFormPage />} />
        <Route path="handovers/:id/edit" element={<HandoverFormPage />} />
        <Route path="borrow/transactions/:id/edit" element={<TransactionFormPage />} />
        {/* <Route path="activity-logs" element={<ActivityLogListPage />} /> */}
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
