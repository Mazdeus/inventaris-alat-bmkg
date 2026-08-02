import api from "./axios";

/**
 * API untuk data peminjam (borrowers).
 */
export const borrowersApi = {
  /**
   * Daftar peminjam.
   * @param {object} params - { page, size, borrower_type, search }
   */
  getBorrowers: (params) => api.get("/borrowers", { params }),

  /**
   * Detail satu peminjam.
   * @param {number} id
   */
  getBorrower: (id) => api.get(`/borrowers/${id}`),

  /**
   * Tambah peminjam baru.
   * @param {object} data - { borrower_type, borrower_name, institution?, phone?, address? }
   */
  createBorrower: (data) => api.post("/borrowers", data),

  /**
   * Update data peminjam.
   * @param {number} id
   * @param {object} data
   */
  updateBorrower: (id, data) => api.put(`/borrowers/${id}`, data),

  /**
   * Hapus banyak peminjam sekaligus.
   * @param {object} data - { ids: number[] }
   */
  bulkDelete: (data) => api.delete("/borrowers/bulk", { data }),
};
