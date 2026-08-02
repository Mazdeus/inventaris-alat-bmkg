import api from "./axios";

export const maintenanceApi = {
  getMaintenances: (params) => api.get("/maintenance", { params }),
  getMaintenance: (id) => api.get(`/maintenance/${id}`),
  createMaintenance: (data) => api.post("/maintenance", data),
  updateMaintenance: (id, data) => api.put(`/maintenance/${id}`, data),
};
