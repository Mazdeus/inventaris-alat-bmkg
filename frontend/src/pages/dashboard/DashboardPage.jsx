import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { dashboardApi } from "@/api/dashboard";
import { useAuth } from "@/contexts/AuthContext";
import StatCard from "@/components/ui/StatCard";
import { CardSkeleton } from "@/components/ui/TableSkeleton";
import {
  Boxes,
  Wrench,
  AlertTriangle,
  ArrowLeftRight,
  BarChart3,
  Trash2,
  Send,
  Lock,
  PackageCheck,
  CheckCircle2,
  Calendar,
  Activity,
  Layers,
  ShoppingBag,
} from "lucide-react";
import { STATUS_LABELS } from "@/lib/constants";
import {
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";

/**
 * Kartu status sekunder ringkas & bersih
 */
function MiniStatusCard({ title, value, icon: Icon, color, bg }) {
  return (
    <div className="group flex items-center gap-3 rounded-2xl border border-slate-200/80 bg-white p-4 shadow-xs transition-all duration-200 hover:border-slate-300 hover:shadow-sm">
      <div className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl transition-transform duration-200 group-hover:scale-105 ${bg}`}>
        <Icon className={`h-5 w-5 ${color}`} />
      </div>
      <div className="min-w-0 flex-1">
        <p className="text-xs font-medium text-slate-500 leading-tight truncate">{title}</p>
        <p className="mt-1 text-xl font-bold tracking-tight text-slate-900 leading-none">
          {typeof value === "number" ? value.toLocaleString("id-ID") : (value ?? 0)}
        </p>
      </div>
    </div>
  );
}

/**
 * Halaman Dashboard Inventaris BMKG
 * Tampilan natural, bersih, dan ringkas mengadopsi referensi modern:
 * - Tidak ada kalimat/paragraf berlebih yang membuat kesan kaku
 * - Tidak ada badge warna berlebihan di header grafik
 * - Grafik tren peminjaman dan pengadaan barang terpisah (masing-masing 12 bulan)
 * - Donut chart dengan ring center label
 */
export default function DashboardPage() {
  const [globalYear, setGlobalYear] = useState("");
  const { isAdmin } = useAuth();

  // Fetch summary
  const {
    data: summaryRes,
    isLoading: summaryLoading,
    isError: summaryError,
  } = useQuery({
    queryKey: ["dashboard", "summary", globalYear],
    queryFn: () => dashboardApi.getSummary(globalYear ? Number(globalYear) : undefined),
  });

  // Fetch charts
  const {
    data: chartsRes,
    isLoading: chartsLoading,
  } = useQuery({
    queryKey: ["dashboard", "charts", globalYear],
    queryFn: () => dashboardApi.getCharts(globalYear ? Number(globalYear) : undefined),
  });

  const summary = summaryRes?.data?.data;
  const charts = chartsRes?.data?.data;
  const isLoadingCharts = chartsLoading;

  const availableYears = summary?.available_years || [
    new Date().getFullYear(),
    new Date().getFullYear() - 1,
  ];

  // Data Donut Chart (Distribusi Status)
  const rawPieData = charts?.status_distribution
    ? charts.status_distribution.labels.map((label, i) => ({
        name: STATUS_LABELS[label] || label,
        value: charts.status_distribution.values[i] || 0,
      }))
    : [];

  const pieData = (isAdmin
    ? rawPieData
    : rawPieData.filter((d) => d.name !== "Dihapuskan")
  ).filter((d) => d.value > 0);

  // Data Grafik 1: Tren Peminjaman (12 bulan Jan - Des)
  const borrowTrendData = charts?.borrow_trend || [];

  // Data Grafik 2: Pengadaan Barang (12 bulan Jan - Des, sama seperti tren peminjaman)
  const procurementMonthlyData = charts?.procurement_by_month || [];

  // Warna palet chart
  const PIE_COLORS = {
    "Tersedia": "#10b981",
    "Ditahan": "#f97316",
    "Dipinjam": "#f59e0b",
    "Perbaikan": "#0284c7",
    "Rusak": "#ef4444",
    "Dihapuskan": "#94a3b8",
    "Dilimpahkan": "#8b5cf6",
  };

  /** Custom tooltip minimalis */
  function ChartTooltip({ active, payload, label }) {
    if (!active || !payload?.length) return null;
    return (
      <div className="rounded-xl border border-slate-200 bg-white px-3.5 py-2.5 shadow-md text-xs">
        <p className="font-semibold text-slate-800 mb-1">{label || payload[0]?.name}</p>
        <div className="space-y-0.5">
          {payload.map((entry, idx) => (
            <div key={idx} className="flex items-center gap-2 text-slate-600">
              <span
                className="h-2 w-2 rounded-full"
                style={{ backgroundColor: entry.color || entry.fill }}
              />
              <span>{entry.name}:</span>
              <span className="font-semibold text-slate-900">{entry.value}</span>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8 pb-10">
      {/* --- Header Dasbor --- */}
      <div className="border-b border-slate-200/80 pb-4">
        <h1 className="text-2xl font-bold tracking-tight text-slate-900">Dasbor</h1>
      </div>

      {/* --- Loading state --- */}
      {summaryLoading && <CardSkeleton count={6} />}

      {/* --- Error state --- */}
      {summaryError && (
        <div className="rounded-2xl border border-red-200 bg-red-50 p-6 text-center text-sm text-red-700 shadow-2xs">
          Gagal memuat data dashboard. Pastikan backend berjalan dengan baik.
        </div>
      )}

      {/* --- Content --- */}
      {!summaryLoading && !summaryError && summary && (
        <>
          {/* ======================================================== */}
          {/* LAPISAN 1: KONDISI STOK FISIK ALAT                       */}
          {/* ======================================================== */}
          <section className="space-y-4">
            <div className="flex items-center gap-2">
              <div className="flex h-6 w-6 items-center justify-center rounded-lg bg-indigo-50 text-indigo-600">
                <Boxes className="h-3.5 w-3.5" />
              </div>
              <h2 className="text-xs font-semibold uppercase tracking-wider text-slate-600">
                Stok Fisik Alat
              </h2>
            </div>

            {/* 4 Kartu Hero Utama */}
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <StatCard
                title="Jenis Unit"
                value={summary.total_components ?? 0}
                subtitle="Katalog tipe alat"
                icon={Layers}
                iconBg="bg-indigo-50"
                iconColor="text-indigo-600"
                colorClass="border-l-indigo-500"
              />
              <StatCard
                title="Total Barang"
                value={summary.total_items ?? 0}
                subtitle="Unit fisik di sistem"
                icon={PackageCheck}
                iconBg="bg-blue-50"
                iconColor="text-blue-600"
                colorClass="border-l-blue-500"
              />
              <StatCard
                title="Barang Tersedia"
                value={summary.status_summary?.available ?? 0}
                subtitle="Siap digunakan"
                icon={CheckCircle2}
                iconBg="bg-emerald-50"
                iconColor="text-emerald-600"
                colorClass="border-l-emerald-500"
              />
              <StatCard
                title="Sedang Dipinjam"
                value={summary.status_summary?.borrowed ?? 0}
                subtitle={`${summary.active_borrows ?? 0} transaksi aktif`}
                icon={ArrowLeftRight}
                iconBg="bg-amber-50"
                iconColor="text-amber-600"
                colorClass="border-l-amber-500"
              />
            </div>

            {/* Sub-status pendukung */}
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-4 lg:grid-cols-5">
              <MiniStatusCard
                title="Perbaikan"
                value={summary.status_summary?.maintenance ?? 0}
                icon={Wrench}
                color="text-sky-600"
                bg="bg-sky-50"
              />
              <MiniStatusCard
                title="Barang Rusak"
                value={summary.status_summary?.broken ?? 0}
                icon={AlertTriangle}
                color="text-rose-600"
                bg="bg-rose-50"
              />
              <MiniStatusCard
                title="Barang Ditahan"
                value={summary.status_summary?.on_hold ?? 0}
                icon={Lock}
                color="text-orange-600"
                bg="bg-orange-50"
              />
              <MiniStatusCard
                title="Dilimpahkan"
                value={summary.status_summary?.transferred ?? 0}
                icon={Send}
                color="text-purple-600"
                bg="bg-purple-50"
              />
              {isAdmin && (
                <MiniStatusCard
                  title="Dihapuskan"
                  value={summary.status_summary?.deleted ?? 0}
                  icon={Trash2}
                  color="text-slate-500"
                  bg="bg-slate-100"
                />
              )}
            </div>
          </section>

          {/* ======================================================== */}
          {/* LAPISAN 2: AKTIVITAS & MUTASI PERIODE (DIFILTER TAHUN)   */}
          {/* ======================================================== */}
          <section className="space-y-4 pt-4 border-t border-slate-200/80">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
              <div className="flex items-center gap-2">
                <div className="flex h-6 w-6 items-center justify-center rounded-lg bg-amber-50 text-amber-600">
                  <Activity className="h-3.5 w-3.5" />
                </div>
                <h2 className="text-xs font-semibold uppercase tracking-wider text-slate-600">
                  Aktivitas Transaksi {globalYear ? `(${globalYear})` : ""}
                </h2>
              </div>

              {/* Filter Periode Transaksi & Grafik */}
              <div className="flex items-center gap-2">
                <span className="text-xs font-medium text-slate-500 hidden sm:inline">Filter Tahun:</span>
                <div className="inline-flex items-center gap-2 rounded-xl border border-slate-200/90 bg-white px-3.5 py-1.5 shadow-2xs">
                  <Calendar className="h-4 w-4 text-slate-400" />
                  <select
                    id="dashboard-year-filter"
                    value={globalYear}
                    onChange={(e) => setGlobalYear(e.target.value)}
                    className="bg-transparent text-xs font-semibold text-slate-700 focus:outline-none cursor-pointer pr-1"
                  >
                    <option value="">Semua Tahun</option>
                    {availableYears.map((y) => (
                      <option key={y} value={y}>Tahun {y}</option>
                    ))}
                  </select>
                </div>
              </div>
            </div>


            {/* 4 Kartu Aktivitas Transaksi */}
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <StatCard
                title="Pelimpahan (UPT)"
                value={summary.period_activity?.handovers ?? 0}
                subtitle="Barang diserahkan"
                icon={Send}
                iconBg="bg-purple-50"
                iconColor="text-purple-600"
                colorClass="border-l-purple-500"
              />
              <StatCard
                title="Peminjaman Baru"
                value={summary.period_activity?.borrows ?? 0}
                subtitle="Transaksi diajukan"
                icon={ArrowLeftRight}
                iconBg="bg-amber-50"
                iconColor="text-amber-600"
                colorClass="border-l-amber-500"
              />
              <StatCard
                title="Pemeliharaan"
                value={summary.period_activity?.maintenances ?? 0}
                subtitle="Servis & kalibrasi"
                icon={Wrench}
                iconBg="bg-sky-50"
                iconColor="text-sky-600"
                colorClass="border-l-sky-500"
              />
              <StatCard
                title="Pengadaan Baru"
                value={summary.period_activity?.procurements ?? 0}
                subtitle="Unit diadakan"
                icon={ShoppingBag}
                iconBg="bg-emerald-50"
                iconColor="text-emerald-600"
                colorClass="border-l-emerald-500"
              />
            </div>
          </section>

          {/* ======================================================== */}
          {/* LAPISAN 3: GRAFIK OPERASIONAL                            */}
          {/* Dipisahkan: Peminjaman (12 bln), Status Donut, Pengadaan (12 bln) */}
          {/* ======================================================== */}
          <section className="space-y-6 pt-2">
            <div className="flex items-center gap-2">
              <div className="flex h-6 w-6 items-center justify-center rounded-lg bg-blue-50 text-blue-600">
                <BarChart3 className="h-3.5 w-3.5" />
              </div>
              <h2 className="text-xs font-semibold uppercase tracking-wider text-slate-600">
                Grafik Operasional
              </h2>
            </div>

            {isLoadingCharts && (
              <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
                <div className="h-80 animate-pulse rounded-2xl border border-slate-200 bg-white" />
                <div className="h-80 animate-pulse rounded-2xl border border-slate-200 bg-white" />
              </div>
            )}

            {!isLoadingCharts && charts && (
              <>
                {/* Baris 1: Tren Peminjaman (Kiri) + Proporsi Status Donut (Kanan) */}
                <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
                  {/* Grafik 1: Tren Peminjaman Bulanan (12 Bulan Jan - Des) */}
                  <div className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-xs flex flex-col justify-between">
                    <div className="border-b border-slate-100 pb-3 mb-2">
                      <h3 className="text-sm font-semibold text-slate-800">
                        Tren Peminjaman {globalYear ? `(${globalYear})` : ""}
                      </h3>
                    </div>

                    {borrowTrendData.length > 0 ? (
                      <ResponsiveContainer width="100%" height={260}>
                        <BarChart data={borrowTrendData}>
                          <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
                          <XAxis
                            dataKey="month"
                            tick={{ fontSize: 11, fill: "#64748b" }}
                            axisLine={{ stroke: "#e2e8f0" }}
                            tickLine={false}
                          />
                          <YAxis
                            tick={{ fontSize: 11, fill: "#64748b" }}
                            allowDecimals={false}
                            axisLine={{ stroke: "#e2e8f0" }}
                            tickLine={false}
                          />
                          <Tooltip content={<ChartTooltip />} />
                          <Bar
                            dataKey="total"
                            name="Peminjaman"
                            fill="#f59e0b"
                            radius={[4, 4, 0, 0]}
                            maxBarSize={28}
                          />
                        </BarChart>
                      </ResponsiveContainer>
                    ) : (
                      <p className="py-16 text-center text-xs text-slate-400">
                        Belum ada data peminjaman
                      </p>
                    )}
                  </div>

                  {/* Grafik 2: Donut Chart Proporsi Status Barang dengan Center Label */}
                  <div className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-xs flex flex-col justify-between">
                    <div className="border-b border-slate-100 pb-3 mb-2">
                      <h3 className="text-sm font-semibold text-slate-800">
                        Status Barang
                      </h3>
                    </div>

                    {pieData.length > 0 ? (
                      <div className="relative flex items-center justify-center">
                        <ResponsiveContainer width="100%" height={260}>
                          <PieChart>
                            <Pie
                              data={pieData}
                              cx="50%"
                              cy="50%"
                              innerRadius={65}
                              outerRadius={96}
                              paddingAngle={3}
                              dataKey="value"
                            >
                              {pieData.map((entry, idx) => (
                                <Cell
                                  key={`cell-${idx}`}
                                  fill={PIE_COLORS[entry.name] || "#cbd5e1"}
                                  stroke="transparent"
                                />
                              ))}
                            </Pie>
                            <Tooltip content={<ChartTooltip />} />
                            <Legend
                              verticalAlign="bottom"
                              iconType="circle"
                              wrapperStyle={{ paddingTop: "12px", fontSize: "11px" }}
                              formatter={(value) => (
                                <span className="text-xs font-medium text-slate-600">{value}</span>
                              )}
                            />
                          </PieChart>
                        </ResponsiveContainer>

                        {/* Center Ring Label */}
                        <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center text-center pb-8">
                          <span className="text-[11px] font-medium text-slate-400">Total</span>
                          <span className="text-2xl font-bold text-slate-900 leading-tight">
                            {(summary.total_items ?? 0).toLocaleString("id-ID")}
                          </span>
                          <span className="text-[10px] text-slate-400">Barang</span>
                        </div>
                      </div>
                    ) : (
                      <p className="py-16 text-center text-xs text-slate-400">
                        Belum ada data distribusi barang
                      </p>
                    )}
                  </div>
                </div>

                {/* Baris 2: Grafik Pengadaan Barang (12 Bulan Jan - Des, Sama seperti Peminjaman) */}
                <div className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-xs flex flex-col justify-between">
                  <div className="border-b border-slate-100 pb-3 mb-2">
                    <h3 className="text-sm font-semibold text-slate-800">
                      Pengadaan Barang {globalYear ? `(${globalYear})` : ""}
                    </h3>
                  </div>

                  {procurementMonthlyData.length > 0 ? (
                    <ResponsiveContainer width="100%" height={240}>
                      <BarChart data={procurementMonthlyData}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
                        <XAxis
                          dataKey="month"
                          tick={{ fontSize: 11, fill: "#64748b" }}
                          axisLine={{ stroke: "#e2e8f0" }}
                          tickLine={false}
                        />
                        <YAxis
                          tick={{ fontSize: 11, fill: "#64748b" }}
                          allowDecimals={false}
                          axisLine={{ stroke: "#e2e8f0" }}
                          tickLine={false}
                        />
                        <Tooltip content={<ChartTooltip />} />
                        <Bar
                          dataKey="total"
                          name="Unit Diadakan"
                          fill="#10b981"
                          radius={[4, 4, 0, 0]}
                          maxBarSize={28}
                        />
                      </BarChart>
                    </ResponsiveContainer>
                  ) : (
                    <p className="py-16 text-center text-xs text-slate-400">
                      Belum ada data pengadaan
                    </p>
                  )}
                </div>
              </>
            )}
          </section>
        </>
      )}
    </div>
  );
}
