import api from "./axios";

/**
 * API untuk autentikasi (login, logout, profil user).
 */
export const authApi = {
  /**
   * Login dengan username dan password.
   * Endpoint: POST /auth/login/json
   * @param {string} username - Username pengguna
   * @param {string} password - Password pengguna
   * @returns {Promise} Response berisi access_token + data user
   */
  login: (username, password) =>
    api.post("/auth/login/json", { username, password }),

  /**
   * Mendapatkan profil user yang sedang login.
   * Endpoint: GET /auth/me
   * @returns {Promise} Response berisi data user (id, username, full_name, role)
   */
  getMe: () => api.get("/auth/me"),

  /**
   * Memperbarui token akses menggunakan refresh token.
   * Endpoint: POST /auth/refresh
   * @param {string} refreshToken - Refresh token yang masih valid
   * @returns {Promise} Response berisi access_token baru
   */
  refreshToken: (refreshToken) =>
    api.post("/auth/refresh", { refresh_token: refreshToken }),

  /**
   * Verifikasi password user yang sedang login (untuk konfirmasi aksi berbahaya).
   * Endpoint: POST /auth/verify-password
   * @param {string} password
   */
  verifyPassword: (password) => api.post("/auth/verify-password", { password }),
};
