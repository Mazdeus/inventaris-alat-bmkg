import { AuthProvider } from "@/contexts/AuthContext";
import AppRouter from "@/router";

/**
 * Komponen root aplikasi.
 * Membungkus seluruh app dengan AuthProvider (context autentikasi)
 * dan AppRouter (konfigurasi route).
 */
export default function App() {
  return (
    <AuthProvider>
      <AppRouter />
    </AuthProvider>
  );
}
