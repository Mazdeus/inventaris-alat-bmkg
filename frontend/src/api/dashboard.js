import api from "./axios";

/**
 * API untuk dashboard — ringkasan statistik dan data grafik.
 */
export const dashboardApi = {
  /**
   * Ringkasan statistik inventaris.
   * Endpoint: GET /dashboard/summary
   * @returns {Promise} data.total_packages, total_components, total_items,
   *   status_summary, active_borrows, pending_approvals, overdue_returns
   */
  getSummary: () => api.get("/dashboard/summary"),

  /**
   * Data untuk grafik dashboard.
   * Endpoint: GET /dashboard/charts
   * @param {number} [year] - Tahun data (default: tahun berjalan)
   * @returns {Promise} data.borrow_trend, status_distribution, procurement_by_year
   */
  getCharts: (year) => api.get("/dashboard/charts", { params: year ? { year } : {} }),
};
