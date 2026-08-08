import api from "./axios";

/**
 * API untuk inventaris — komponen dan item.
 */
export const inventoryApi = {
  // ═══════════ Components ═══════════

  /**
   * Daftar komponen inventaris.
   * @param {object} params - { page, size, search, status_id, procurement_year }
   */
  getComponents: (params) => api.get("/inventory/components", { params }),

  /**
   * Detail satu komponen.
   * @param {number} id - ID komponen
   */
  getComponent: (id) => api.get(`/inventory/components/${id}`),

  /**
   * Tambah komponen baru.
   * @param {object} data - { item_name, brand?, ... }
   */
  createComponent: (data) => api.post("/inventory/components", data),

  /**
   * Update komponen.
   * @param {number} id - ID komponen
   * @param {object} data - Field yang mau diupdate (partial)
   */
  updateComponent: (id, data) => api.put(`/inventory/components/${id}`, data),

  /**
   * Hapus komponen.
   * @param {number} id - ID komponen
   */
  deleteComponent: (id) => api.delete(`/inventory/components/${id}`),

  /**
   * Daftar status komponen (untuk dropdown filter).
   */
  getStatuses: () => api.get("/inventory/statuses"),

  // ═══════════ Items (per barang fisik) ═══════════

  /** Daftar semua barang individual lintas unit. */
  getAllItems: (params) => api.get("/inventory/items", { params }),

  /** Daftar item individual dalam satu komponen. */
  getItems: (componentId) => api.get(`/inventory/components/${componentId}/items`),

  /** Update serial number item. */
  updateItem: (itemId, data) => api.put(`/inventory/items/${itemId}`, data),

  /** Hapus item individual (soft delete). */
  deleteItem: (itemId) => api.delete(`/inventory/items/${itemId}`),

  /** Riwayat perubahan status item. */
  getItemHistory: (itemId) => api.get(`/inventory/items/${itemId}/history`),

  // ═══════════ Template & Import ═══════════

  /**
   * Download template Excel (.xlsx).
   * Returns blob response.
   */
  downloadTemplate: () => api.get("/inventory/components/template", { responseType: "blob" }),

  /**
   * Import komponen dari file Excel.
   * @param {File} file - File .xlsx
   */
  importComponents: (file) => {
    const formData = new FormData();
    formData.append("file", file);
    return api.post("/inventory/components/import", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },
};
