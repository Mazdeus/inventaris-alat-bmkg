import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { dashboardApi } from "@/api/dashboard";
import { useAuth } from "@/contexts/AuthContext";
import StatCard from "@/components/ui/StatCard";
import { CardSkeleton } from "@/components/ui/TableSkeleton";
import PageHeader from "@/components/ui/PageHeader";
import {
  Boxes, Wrench, AlertTriangle, ArrowLeftRight, Clock, BarChart3,
  Trash2, Send, Lock,
} from "lucide-react";
import { CHART_COLORS, STAT_CARD_BORDER, STATUS_LABELS } from "@/lib/constants";
import {
  PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Legend,
} from "recharts";

/**
 * Halaman dashboard — ringkasan statistik, grafik status, tren peminjaman.
 * Data dari endpoint /dashboard/summary dan /dashboard/charts.
 * Terdapat filter tahun global di paling atas yang memengaruhi seluruh card & grafik.
 */
export default function DashboardPage() {
  const [globalYear, setGlobalYear] = useState(new Date().getFullYear());
  const { isAdmin } = useAuth();

  // Fetch summary — difilter tahun global
  const {
    data: summaryRes,
    isLoading: summaryLoading,
    isError: summaryError,
  } = useQuery({
    queryKey: ["dashboard", "summary", globalYear],
    queryFn: () => dashboardApi.getSummary(globalYear),
  });

  // Fetch charts — tren peminjaman + pengadaan per bulan (tahun global)
  const {
    data: chartsRes,
    isLoading: chartsLoading,
  } = useQuery({
    queryKey: ["dashboard", "charts", globalYear],
    queryFn: () => dashboardApi.getCharts(globalYear),
  });

  const summary = summaryRes?.data?.data;
  const charts = chartsRes?.data?.data;
  const isLoadingCharts = chartsLoading;

  // Data untuk pie chart (distribusi status)
  // Admin: semua status, non-admin: tanpa Dihapuskan & Dilimpahkan
  const rawPieData = charts?.status_distribution
    ? charts.status_distribution.labels.map((label, i) => ({
        name: STATUS_LABELS[label] || label,
        value: charts.status_distribution.values[i],
      }))
    : [];
  const pieData = isAdmin
    ? rawPieData
    : rawPieData.filter((d) => d.name !== "Dihapuskan" && d.name !== "Dilimpahkan");

  // Data untuk bar chart (tren peminjaman)
  const barData = charts?.borrow_trend || [];

  // Data untuk bar chart (pengadaan per bulan)
  const procurementData = charts?.procurement_by_month || [];

  // Warna untuk pie chart slices (berdasarkan nama status)
  const PIE_COLORS = {
    "Tersedia": "#10b981",
    "Ditahan": "#f59e0b",
    "Dipinjam": "#f97316",
    "Perbaikan": "#3b82f6",
    "Rusak": "#ef4444",
    "Dihapuskan": "#9ca3af",
    "Dilimpahkan": "#a855f7",
  };

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

      {/* --- Filter tahun global --- */}
      <div className="mb-6 flex flex-wrap items-center gap-3 rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
        <div className="flex items-center gap-2">
          <BarChart3 className="h-4 w-4 text-gray-400" />
          <span className="text-sm font-medium text-gray-700">Tahun Data</span>
        </div>
        <select
          value={globalYear}
          onChange={(e) => setGlobalYear(Number(e.target.value))}
          className="rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-700 focus:outline-none focus:ring-2 focus:ring-slate-400"
        >
          {Array.from({ length: 10 }, (_, i) => {
            const y = new Date().getFullYear() - i;
            return <option key={y} value={y}>{y}</option>;
          })}
        </select>
        <span className="text-xs text-gray-400">
          Seluruh kartu dan grafik menyesuaikan tahun yang dipilih.
        </span>
      </div>

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

          {/* Baris 2: Detail status — per barang */}
          <div className="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <StatCard
              title="Barang Tersedia"
              value={summary.status_summary?.available ?? 0}
              colorClass={STAT_CARD_BORDER.available}
            />
            <StatCard
              title="Barang Ditahan"
              subtitle="dalam proses transaksi"
              value={summary.status_summary?.ditahan ?? 0}
              colorClass="border-l-amber-500"
              icon={Lock}
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
              subtitle="peminjaman pending"
              value={summary.pending_approvals ?? 0}
              colorClass={STAT_CARD_BORDER.pending}
              icon={Clock}
            />
          </div>

          {/* Baris admin only: Dihapuskan & Dilimpahkan */}
          {isAdmin && (
            <div className="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-2">
              <StatCard
                title="Barang Dihapuskan"
                subtitle="soft-delete"
                value={summary.status_summary?.dihapuskan ?? 0}
                colorClass="border-l-gray-400"
                icon={Trash2}
              />
              <StatCard
                title="Barang Dilimpahkan"
                subtitle="diserahkan ke UPT"
                value={summary.status_summary?.dilimpahkan ?? 0}
                colorClass="border-l-purple-500"
                icon={Send}
              />
            </div>
          )}

          {/* --- Charts --- */}
          {isLoadingCharts && (
            <div className="mb-6 grid grid-cols-1 gap-6 lg:grid-cols-2">
              <div className="h-80 animate-pulse rounded-lg border border-gray-200 bg-white" />
              <div className="h-80 animate-pulse rounded-lg border border-gray-200 bg-white" />
            </div>
          )}

          {!isLoadingCharts && charts && (
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
                              fill={PIE_COLORS[entry.name] || "#cbd5e1"}
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
                  <h3 className="mb-4 text-sm font-semibold text-gray-700">
                    Tren Peminjaman {globalYear}
                  </h3>
                  {barData.length > 0 ? (
                    <ResponsiveContainer width="100%" height={280}>
                      <BarChart data={barData}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                        <XAxis dataKey="month" tick={{ fontSize: 12 }} label={{ value: "Bulan", position: "insideBottom", offset: -5, style: { fontSize: 12, fill: "#6b7280" } }} />
                        <YAxis tick={{ fontSize: 12 }} allowDecimals={false} label={{ value: "Jumlah", angle: -90, position: "insideLeft", offset: 0, style: { fontSize: 12, fill: "#6b7280" } }} />
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

              {/* Row 2: Bar chart — pengadaan per bulan */}
              <div className="rounded-lg border border-gray-200 bg-white p-5 shadow-sm">
                <h3 className="mb-4 text-sm font-semibold text-gray-700">
                  Pengadaan {globalYear}
                </h3>
                {procurementData.length > 0 ? (
                  <ResponsiveContainer width="100%" height={250}>
                    <BarChart data={procurementData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                      <XAxis dataKey="month" tick={{ fontSize: 12 }} label={{ value: "Bulan", position: "insideBottom", offset: -5, style: { fontSize: 12, fill: "#6b7280" } }} />
                      <YAxis tick={{ fontSize: 12 }} allowDecimals={false} label={{ value: "Jumlah", angle: -90, position: "insideLeft", style: { fontSize: 12, fill: "#6b7280" } }} />
                      <Tooltip content={<ChartTooltip />} />
                      <Bar dataKey="total" fill={CHART_COLORS.available} radius={[4, 4, 0, 0]} name="Item Diadakan" />
                    </BarChart>
                  </ResponsiveContainer>
                ) : (
                  <p className="py-12 text-center text-sm text-gray-400">
                    Belum ada data pengadaan untuk tahun ini
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
