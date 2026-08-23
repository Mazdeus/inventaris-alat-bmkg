import api from "./axios";

/**
 * API untuk data petugas (officers).
 */
export const officersApi = {
  /**
   * Daftar petugas.
   * @param {object} params - { page, size, search, is_active }
   */
  getOfficers: (params) => api.get("/officers", { params }),

  /**
   * Detail satu petugas.
   * @param {number} id
   */
  getOfficer: (id) => api.get(`/officers/${id}`),

  /**
   * Tambah petugas baru.
   * @param {object} data - { officer_name, phone?, email?, position? }
   */
  createOfficer: (data) => api.post("/officers", data),

  /**
   * Update data petugas.
   * @param {number} id
   * @param {object} data
   */
  updateOfficer: (id, data) => api.put(`/officers/${id}`, data),

  /**
   * Hapus petugas.
   * @param {number} id
   */
  deleteOfficer: (id) => api.delete(`/officers/${id}`),
};
