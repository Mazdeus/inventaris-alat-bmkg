import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { dashboardApi } from "@/api/dashboard";
import StatCard from "@/components/ui/StatCard";
import { CardSkeleton } from "@/components/ui/TableSkeleton";
import PageHeader from "@/components/ui/PageHeader";
import {
  Boxes, Wrench, AlertTriangle, ArrowLeftRight, Clock, BarChart3,
} from "lucide-react";
import { CHART_COLORS, STAT_CARD_BORDER, STATUS_LABELS } from "@/lib/constants";
import {
  PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, LineChart, Line, Legend,
} from "recharts";
import { formatDate } from "@/lib/formatters";

/**
 * Halaman dashboard — ringkasan statistik, grafik status, tren peminjaman.
 * Data dari endpoint /dashboard/summary dan /dashboard/charts.
 */
export default function DashboardPage() {
  const [chartYear, setChartYear] = useState(new Date().getFullYear());

  // Fetch summary
  const {
    data: summaryRes,
    isLoading: summaryLoading,
    isError: summaryError,
  } = useQuery({
    queryKey: ["dashboard", "summary"],
    queryFn: () => dashboardApi.getSummary(),
  });

  // Fetch charts
  const {
    data: chartsRes,
    isLoading: chartsLoading,
  } = useQuery({
    queryKey: ["dashboard", "charts", chartYear],
    queryFn: () => dashboardApi.getCharts(chartYear),
  });

  const summary = summaryRes?.data?.data;
  const charts = chartsRes?.data?.data;

  // Data untuk pie chart (distribusi status)
  const pieData = charts?.status_distribution
    ? charts.status_distribution.labels.map((label, i) => ({
        name: STATUS_LABELS[label] || label,
        value: charts.status_distribution.values[i],
      }))
    : [];

  // Data untuk bar chart (tren peminjaman)
  const barData = charts?.borrow_trend || [];

  // Data untuk line chart (pengadaan per tahun)
  const lineData = charts?.procurement_by_year || [];

  // Warna untuk pie chart slices
  const PIE_COLORS = [
    CHART_COLORS.available,
    CHART_COLORS.borrowed,
    CHART_COLORS.maintenance,
    CHART_COLORS.broken,
  ];

  /** Custom tooltip untuk chart (format number dengan pemisah ribuan) */
  function ChartTooltip({ active, payload, label }) {
    if (!active || !payload?.length) return null;
    return (
      <div className="rounded-md border border-gray-200 bg-white p-3 shadow-md text-sm">
        <p className="font-semibold text-gray-700">{label || payload[0]?.name}</p>
        {payload.map((entry, idx) => (
          <p key={idx} className="text-gray-600">
            {entry.name}: <span className="font-medium">{entry.value}</span>
          </p>
        ))}
      </div>
    );
  }

  return (
    <div>
      <PageHeader title="Dasbor" description="Ringkasan inventaris alat sensor BMKG" />

      {/* --- Loading state --- */}
      {summaryLoading && <CardSkeleton count={6} />}

      {/* --- Error state --- */}
      {summaryError && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-6 text-center text-red-700">
          Gagal memuat data dashboard. Pastikan backend berjalan.
        </div>
      )}

      {/* --- Stat cards --- */}
      {!summaryLoading && !summaryError && summary && (
        <>
          {/* Baris 1: Ringkasan utama */}
          <div className="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <StatCard
              title="Jenis Unit"
              subtitle="per jenis/tipe"
              value={summary.total_components ?? 0}
              icon={Boxes}
              colorClass="border-l-blue-500"
            />
            <StatCard
              title="Total Barang"
              subtitle="jumlah fisik semua item"
              value={summary.total_items ?? 0}
              icon={BarChart3}
              colorClass="border-l-violet-500"
            />
            <StatCard
              title="Transaksi Aktif"
              subtitle="jumlah peminjaman berjalan"
              value={summary.active_borrows ?? 0}
              icon={ArrowLeftRight}
              colorClass={STAT_CARD_BORDER.borrowed}
            />
          </div>

          {/* Baris 2: Detail status — per barang (total quantity) */}
          <div className="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-5">
            <StatCard
              title="Barang Tersedia"
              value={summary.status_summary?.available ?? 0}
              colorClass={STAT_CARD_BORDER.available}
            />
            <StatCard
              title="Sedang Dipinjam"
              subtitle="jumlah barang dipinjam"
              value={summary.status_summary?.borrowed ?? 0}
              colorClass={STAT_CARD_BORDER.borrowed}
            />
            <StatCard
              title="Dalam Perbaikan"
              value={summary.status_summary?.maintenance ?? 0}
              colorClass={STAT_CARD_BORDER.maintenance}
              icon={Wrench}
            />
            <StatCard
              title="Barang Rusak"
              value={summary.status_summary?.broken ?? 0}
              colorClass={STAT_CARD_BORDER.broken}
              icon={AlertTriangle}
            />
            <StatCard
              title="Menunggu Persetujuan"
              subtitle="peminjam eksternal"
              value={summary.pending_approvals ?? 0}
              colorClass={STAT_CARD_BORDER.pending}
              icon={Clock}
            />
          </div>

          {/* --- Charts --- */}
          {chartsLoading && (
            <div className="mb-6 grid grid-cols-1 gap-6 lg:grid-cols-2">
              <div className="h-80 animate-pulse rounded-lg border border-gray-200 bg-white" />
              <div className="h-80 animate-pulse rounded-lg border border-gray-200 bg-white" />
            </div>
          )}

          {!chartsLoading && charts && (
            <>
              {/* Row 1: Pie + Bar */}
              <div className="mb-6 grid grid-cols-1 gap-6 lg:grid-cols-2">
                {/* Pie chart — distribusi status */}
                <div className="rounded-lg border border-gray-200 bg-white p-5 shadow-sm">
                  <h3 className="mb-4 text-sm font-semibold text-gray-700">
                    Distribusi Status Barang
                  </h3>
                  {pieData.length > 0 ? (
                    <ResponsiveContainer width="100%" height={280}>
                      <PieChart>
                        <Pie
                          data={pieData}
                          cx="50%"
                          cy="50%"
                          innerRadius={60}
                          outerRadius={100}
                          paddingAngle={3}
                          dataKey="value"
                        >
                          {pieData.map((entry, idx) => (
                            <Cell
                              key={`cell-${idx}`}
                              fill={PIE_COLORS[idx % PIE_COLORS.length]}
                            />
                          ))}
                        </Pie>
                        <Tooltip content={<ChartTooltip />} />
                        <Legend
                          verticalAlign="bottom"
                          height={36}
                          formatter={(value) => (
                            <span className="text-sm text-gray-600">{value}</span>
                          )}
                        />
                      </PieChart>
                    </ResponsiveContainer>
                  ) : (
                    <p className="py-12 text-center text-sm text-gray-400">
                      Belum ada data distribusi
                    </p>
                  )}
                </div>

                {/* Bar chart — tren peminjaman */}
                <div className="rounded-lg border border-gray-200 bg-white p-5 shadow-sm">
                  <div className="mb-4 flex items-center justify-between">
                    <h3 className="text-sm font-semibold text-gray-700">
                      Tren Peminjaman {chartYear}
                    </h3>
                    <select
                      value={chartYear}
                      onChange={(e) => setChartYear(Number(e.target.value))}
                      className="rounded-md border border-gray-300 bg-white px-2 py-1 text-xs text-gray-600"
                    >
                      {Array.from({ length: 5 }, (_, i) => {
                        const y = new Date().getFullYear() - i;
                        return (
                          <option key={y} value={y}>
                            {y}
                          </option>
                        );
                      })}
                    </select>
                  </div>
                  {barData.length > 0 ? (
                    <ResponsiveContainer width="100%" height={280}>
                      <BarChart data={barData}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                        <XAxis dataKey="month" tick={{ fontSize: 12 }} />
                        <YAxis tick={{ fontSize: 12 }} allowDecimals={false} />
                        <Tooltip content={<ChartTooltip />} />
                        <Bar
                          dataKey="total"
                          fill={CHART_COLORS.maintenance}
                          radius={[4, 4, 0, 0]}
                          name="Peminjaman"
                        />
                      </BarChart>
                    </ResponsiveContainer>
                  ) : (
                    <p className="py-12 text-center text-sm text-gray-400">
                      Belum ada data peminjaman di tahun ini
                    </p>
                  )}
                </div>
              </div>

              {/* Row 2: Line chart — pengadaan */}
              <div className="rounded-lg border border-gray-200 bg-white p-5 shadow-sm">
                <h3 className="mb-4 text-sm font-semibold text-gray-700">
                  Pengadaan per Tahun
                </h3>
                {lineData.length > 0 ? (
                  <ResponsiveContainer width="100%" height={250}>
                    <LineChart data={lineData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                      <XAxis dataKey="year" tick={{ fontSize: 12 }} />
                      <YAxis tick={{ fontSize: 12 }} allowDecimals={false} />
                      <Tooltip content={<ChartTooltip />} />
                      <Legend />
                      <Line
                        type="monotone"
                        dataKey="total"
                        stroke={CHART_COLORS.available}
                        strokeWidth={2}
                        dot={{ r: 4, fill: CHART_COLORS.available }}
                        activeDot={{ r: 6 }}
                        name="Jumlah Item"
                      />
                    </LineChart>
                  </ResponsiveContainer>
                ) : (
                  <p className="py-12 text-center text-sm text-gray-400">
                    Belum ada data pengadaan
                  </p>
                )}
              </div>
            </>
          )}
        </>
      )}
    </div>
  );
}
