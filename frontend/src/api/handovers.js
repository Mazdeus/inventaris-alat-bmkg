import api from "./axios";

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
  uploadDocument: (id, file) => {
    const formData = new FormData();
    formData.append("file", file);
    return api.post(`/handovers/${id}/document`, formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },
};
