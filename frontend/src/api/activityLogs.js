import api from "./axios";

export const activityLogsApi = {
  getLogs: (params) => api.get("/activity-logs", { params }),
  getLog: (id) => api.get(`/activity-logs/${id}`),
};
