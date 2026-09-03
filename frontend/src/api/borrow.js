import api from "./axios";
import { compressImage } from "@/lib/imageCompressor";


/**
 * API untuk transaksi peminjaman.
 */
export const borrowApi = {
  /**
   * Daftar transaksi peminjaman.
   * @param {object} params - { page, size, start_date, end_date, borrower_name, status }
   */
  getTransactions: (params) => api.get("/borrow/transactions", { params }),

  /**
   * Detail transaksi + rincian komponen yang dipinjam.
   * @param {number} id
   */
  getTransaction: (id) => api.get(`/borrow/transactions/${id}`),

  /**
   * Buat transaksi peminjaman baru.
   * @param {object} data - { borrower_id, borrow_date, expected_return_date, details: [{inventory_component_id, quantity, inventory_item_ids: [...]}] }
   */
  createTransaction: (data) => api.post("/borrow/transactions", data),

  /**
   * Setujui peminjaman (Admin only).
   * @param {number} id
   */
  approve: (id) => api.put(`/borrow/transactions/${id}/approve`),

  /**
   * Tolak peminjaman (Admin only).
   * @param {number} id
   * @param {string} [reason] - Alasan penolakan
   */
  reject: (id, reason) => api.put(`/borrow/transactions/${id}/reject`, { reason }),

  /**
   * Batalkan transaksi (Admin only).
   * @param {number} id
   */
  cancel: (id) => api.put(`/borrow/transactions/${id}/cancel`),

  /**
   * Update transaksi peminjaman (Admin only).
   * @param {number} id
   * @param {object} data
   */
  updateTransaction: (id, data) => api.put(`/borrow/transactions/${id}`, data),

  /**
   * Hapus transaksi massal (Admin only).
   * @param {number[]} ids - Daftar ID transaksi yang akan dihapus
   */
  bulkDelete: (ids) => api.delete("/borrow/transactions/bulk", { data: { ids } }),

  /**
   * Download dokumen peminjaman.
   * @param {number} id
   */
  downloadDocument: (id) => api.get(`/borrow/transactions/${id}/document`, { responseType: "blob" }),

  /**
   * Upload dokumen yang sudah ditandatangani.
   * @param {number} id
   * @param {File} file
   */
  uploadDocument: async (id, file) => {
    const processedFile = await compressImage(file);
    const formData = new FormData();
    formData.append("file", processedFile);
    return api.post(`/borrow/transactions/${id}/document`, formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },



  // ── Perpanjangan Peminjaman ──

  /**
   * Ajukan perpanjangan peminjaman.
   * @param {number} borrowId
   * @param {object} data - { requested_return_date, reason }
   */
  requestExtension: (borrowId, data) => api.post(`/borrow/transactions/${borrowId}/extensions`, data),

  /**
   * Daftar riwayat perpanjangan.
   * @param {number} borrowId
   */
  getExtensions: (borrowId) => api.get(`/borrow/transactions/${borrowId}/extensions`),

  /**
   * Setujui perpanjangan (Admin only).
   * @param {number} borrowId
   * @param {number} extensionId
   */
  approveExtension: (borrowId, extensionId) => api.put(`/borrow/transactions/${borrowId}/extensions/${extensionId}/approve`),

  /**
   * Tolak perpanjangan (Admin only).
   * @param {number} borrowId
   * @param {number} extensionId
   */
  rejectExtension: (borrowId, extensionId) => api.put(`/borrow/transactions/${borrowId}/extensions/${extensionId}/reject`),
};
