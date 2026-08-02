import { Navigate } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";

/**
 * Membungkus halaman yang butuh autentikasi (opsional).
 * - Jika requireAuth = true → user harus login, jika tidak → redirect ke /login.
 * - Jika adminOnly = true → user harus login + role Admin.
 * - Jika adminOnly = false dan requireAuth = false → public read-only (no redirect).
 *
 * @param {object} props
 * @param {React.ReactNode} props.children
 * @param {boolean} [props.adminOnly=false]
 * @param {boolean} [props.requireAuth=false] - Hanya boleh diakses user yang login
 */
export function ProtectedRoute({ children, adminOnly = false, requireAuth = false }) {
  const { isAuthenticated, isAdmin, loading } = useAuth();

  // Tampilkan spinner kecil saat loading (pertama kali mount)
  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center bg-gray-50">
        <div className="h-10 w-10 animate-spin rounded-full border-4 border-slate-300 border-t-slate-600" />
      </div>
    );
  }

  // requireAuth: harus login dulu
  if ((requireAuth || adminOnly) && !isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  // Admin-only: sudah login tapi bukan Admin
  if (adminOnly && !isAdmin) {
    return <Navigate to="/" replace />;
  }

  // Public atau authenticated: render langsung
  return children;
}
