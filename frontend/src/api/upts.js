import api from "./axios";

/**
 * API untuk data Unit Pelaksana Teknis (UPT).
 */
export const uptsApi = {
  /**
   * Daftar UPT dengan pagination dan pencarian.
   * @param {object} params - { page, size, search, is_active }
   */
  getUpts: (params) => api.get("/upts", { params }),

  /**
   * Detail satu UPT.
   * @param {number} id
   */
  getUpt: (id) => api.get(`/upts/${id}`),

  /**
   * Tambah UPT baru.
   * @param {object} data - { name, address?, phone?, is_active? }
   */
  createUpt: (data) => api.post("/upts", data),

  /**
   * Update data UPT.
   * @param {number} id
   * @param {object} data
   */
  updateUpt: (id, data) => api.put(`/upts/${id}`, data),

  /**
   * Hapus UPT (soft delete).
   * @param {number} id
   */
  deleteUpt: (id) => api.delete(`/upts/${id}`),
};
