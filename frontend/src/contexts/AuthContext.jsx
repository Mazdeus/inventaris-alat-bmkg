import { createContext, useContext, useState, useEffect, useCallback } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { authApi } from "@/api/auth";

/**
 * Context untuk autentikasi.
 * Menyediakan: user, isAuthenticated, isAdmin, loading, login, logout, refresh
 * ke seluruh komponen di dalam AuthProvider.
 */
const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const queryClient = useQueryClient();
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // Cek sessionStorage saat pertama kali mount (refresh/buka tab baru)
  useEffect(() => {
    const token = sessionStorage.getItem("access_token");
    const savedUser = sessionStorage.getItem("user");
    if (token && savedUser) {
      try {
        setUser(JSON.parse(savedUser));
      } catch {
        // Data corrupt — bersihkan
        sessionStorage.removeItem("user");
      }
    }
    setLoading(false);
  }, []);

  /**
   * Login — mengirim kredensial ke backend, menyimpan token + user + refresh_token.
   */
  const login = useCallback(async (username, password) => {
    const res = await authApi.login(username, password);
    const { access_token, refresh_token, user: userData } = res.data;
    sessionStorage.setItem("access_token", access_token);
    sessionStorage.setItem("refresh_token", refresh_token);
    sessionStorage.setItem("user", JSON.stringify(userData));
    setUser(userData);
    return userData;
  }, []);

  /**
   * Refresh token — panggil /auth/refresh untuk dapat token baru.
   * Return true jika sukses, false jika gagal.
   */
  const refresh = useCallback(async () => {
    const refreshToken = sessionStorage.getItem("refresh_token");
    if (!refreshToken) return false;
    try {
      const res = await authApi.refreshToken(refreshToken);
      const { access_token, refresh_token, user: userData } = res.data;
      sessionStorage.setItem("access_token", access_token);
      sessionStorage.setItem("refresh_token", refresh_token);
      sessionStorage.setItem("user", JSON.stringify(userData));
      setUser(userData);
      return true;
    } catch {
      // Refresh gagal — logout
      sessionStorage.removeItem("access_token");
      sessionStorage.removeItem("refresh_token");
      sessionStorage.removeItem("user");
      setUser(null);
      return false;
    }
  }, []);

  /**
   * Logout — menghapus token dan user dari sessionStorage + state.
   */
  const logout = useCallback(() => {
    sessionStorage.removeItem("access_token");
    sessionStorage.removeItem("refresh_token");
    sessionStorage.removeItem("user");
    setUser(null);
    queryClient.clear(); // hapus semua cache query dari sesi sebelumnya
  }, [queryClient]);

  // Proactive token rotation — setiap 10 menit
  useEffect(() => {
    if (!user) return;
    const interval = setInterval(() => {
      refresh();
    }, 10 * 60 * 1000); // 10 menit
    return () => clearInterval(interval);
  }, [user, refresh]);

  const value = {
    user,
    isAuthenticated: !!user,
    isAdmin: user?.role === "Admin",
    loading,
    login,
    logout,
    refresh,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

/**
 * Custom hook untuk mengakses AuthContext.
 * @returns {{ user, isAuthenticated, isAdmin, loading, login, logout, refresh }}
 */
export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth() harus digunakan di dalam <AuthProvider>");
  }
  return ctx;
}
