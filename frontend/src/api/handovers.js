import api from "./axios";
import { compressImage } from "@/lib/imageCompressor";

export const handoversApi = {
  /** Daftar pelimpahan */
  getHandovers: (params) => api.get("/handovers", { params }),

  /** Detail pelimpahan */
  getHandover: (id) => api.get(`/handovers/${id}`),

  /** Buat pelimpahan baru */
  createHandover: (data) => api.post("/handovers", data),

  /** Complete (Draft → Dilimpahkan) */
  completeHandover: (id) => api.put(`/handovers/${id}/complete`),

  /** Cancel (Draft → Dibatalkan) */
  cancelHandover: (id) => api.put(`/handovers/${id}/cancel`),

  /** Download dokumen dummy */
  downloadDocument: (id) => api.get(`/handovers/${id}/document`, { responseType: "blob" }),

  /** Upload dokumen tertandatangan */
  uploadDocument: async (id, file) => {
    const processedFile = await compressImage(file);
    const formData = new FormData();
    formData.append("file", processedFile);
    return api.post(`/handovers/${id}/document`, formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },



  /** Hapus pelimpahan — Admin only. Hanya Draft. */
  deleteHandover: (id) => api.delete(`/handovers/${id}`),

  /** Update pelimpahan — Admin only. Hanya Draft. */
  updateHandover: (id, data) => api.put(`/handovers/${id}`, data),
};
