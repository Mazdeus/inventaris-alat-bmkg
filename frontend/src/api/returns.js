import api from "./axios";
import { compressImage } from "@/lib/imageCompressor";

/**
 * API untuk transaksi pengembalian.
 */
export const returnsApi = {
  /**
   * Daftar pengembalian.
   * @param {object} params - { page, size, start_date, end_date }
   */
  getReturns: (params) => api.get("/returns", { params }),

  /**
   * Detail pengembalian + rincian per barang.
   * @param {number} id
   */
  getReturn: (id) => api.get(`/returns/${id}`),

  /**
   * Proses pengembalian baru.
   * @param {object} data - { borrow_id, received_by?, return_date, photo?, late_reason?, details: [{inventory_component_id, items: [{inventory_item_id, condition, notes}]}] }
   */
  createReturn: (data) => api.post("/returns", data),

  /**
   * Download template dokumen pengembalian.
   * @param {number} id
   */
  downloadDocument: (id) => api.get(`/returns/${id}/document`, { responseType: "blob" }),

  /**
   * Upload dokumen pengembalian yang sudah ditandatangani.
   * @param {number} id
   * @param {File} file
   */
  uploadDocument: async (id, file) => {
    const processedFile = await compressImage(file);
    const formData = new FormData();
    formData.append("file", processedFile);
    return api.post(`/returns/${id}/document`, formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },



  /**
   * Verifikasi pengembalian — Admin only.
   * @param {number} id
   */
  verifyReturn: (id) => api.put(`/returns/${id}/verify`),

  /**
   * Tolak pengembalian — Admin only.
   * @param {number} id
   */
  rejectReturn: (id) => api.put(`/returns/${id}/reject`),

  /**
   * Hapus pengembalian — Admin only.
   * @param {number} id
   */
  deleteReturn: (id) => api.delete(`/returns/${id}`),

  /**
   * Update pengembalian — Admin only.
   * @param {number} id
   * @param {object} data
   */
  updateReturn: (id, data) => api.put(`/returns/${id}`, data),
};
