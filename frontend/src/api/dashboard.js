import api from "./axios";

/**
 * API untuk dashboard — ringkasan statistik dan data grafik.
 */
export const dashboardApi = {
  /**
   * Ringkasan statistik inventaris.
   * Endpoint: GET /dashboard/summary
   * @param {number} [year] - Tahun data (opsional)
   */
  getSummary: (year) => api.get("/dashboard/summary", { params: year ? { year } : {} }),

  /**
   * Data untuk grafik dashboard.
   * Endpoint: GET /dashboard/charts
   * @param {number} [year] - Tahun data (default: tahun berjalan)
   * @returns {Promise} data.borrow_trend, status_distribution, procurement_by_year
   */
  getCharts: (year) => api.get("/dashboard/charts", { params: year ? { year } : {} }),
};
