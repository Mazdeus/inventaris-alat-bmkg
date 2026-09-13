import { useState, useMemo } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useAuth } from "@/contexts/AuthContext";
import { maintenanceApi } from "@/api/maintenance";
import { inventoryApi } from "@/api/inventory";
import DataTable from "@/components/ui/DataTable";
import PageHeader from "@/components/ui/PageHeader";
import FilterBar from "@/components/ui/FilterBar";
import StatusBadge from "@/components/ui/StatusBadge";
import MaintenanceForm from "./MaintenanceForm";
import { formatDate } from "@/lib/formatters";
import { STATUS_LABELS } from "@/lib/constants";
import { Plus, Pencil, ArrowUp, ArrowDown } from "lucide-react";
import DatePresetFilter from "@/components/ui/DatePresetFilter";

const MAINTENANCE_COLORS = {
  "In Progress": "bg-orange-100 text-orange-800",
  Completed: "bg-emerald-100 text-emerald-800",
  Cancelled: "bg-gray-100 text-gray-600",
};

export default function MaintenanceListPage() {
  const queryClient = useQueryClient();
  const { isAdmin } = useAuth();
  const [page, setPage] = useState(1);
  const [filterComp, setFilterComp] = useState(null);
  const [filterStatus, setFilterStatus] = useState(null);
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [sortOrder, setSortOrder] = useState("asc");
  const [formOpen, setFormOpen] = useState(false);
  const [editData, setEditData] = useState(null);

  const { data, isLoading, isError } = useQuery({
    queryKey: ["maintenance", page, filterComp, filterStatus, startDate, endDate, sortOrder],
    queryFn: () =>
      maintenanceApi.getMaintenances({
        page,
        size: 10,
        component_id: filterComp || undefined,
        status: filterStatus || undefined,
        start_date: startDate || undefined,
        end_date: endDate || undefined,
        order_dir: sortOrder,
      }),
    keepPreviousData: true,
  });

  const { data: compsRes } = useQuery({
    queryKey: ["components", "all"],
    queryFn: () => inventoryApi.getComponents({ size: 100 }),
    staleTime: 5 * 60_000,
  });

  const maints = data?.data?.data || [];
  const meta = data?.data?.meta;
  const components = compsRes?.data?.data || [];

  const displayedMaints = useMemo(() => {
    if (!maints || maints.length === 0) return [];
    const total = meta?.total ?? maints.length;
    return maints.map((item, idx) => ({
      ...item,
      __rowNumber: sortOrder === "desc"
        ? total - ((page - 1) * 10 + idx)
        : (page - 1) * 10 + idx + 1,
    }));
  }, [maints, page, sortOrder, meta?.total]);

  const columns = [
    {
      key: "no",
      header: (
        <button
          type="button"
          onClick={() => {
            setSortOrder((prev) => (prev === "asc" ? "desc" : "asc"));
            setPage(1);
          }}
          className="flex items-center gap-1 hover:text-slate-900 transition-colors cursor-pointer group"
          title={`Urutkan: ${sortOrder === "asc" ? "Menaik (Ascending) - Klik untuk Menurun" : "Menurun (Descending) - Klik untuk Menaik"}`}
        >
          <span>No.</span>
          {sortOrder === "asc" ? (
            <ArrowUp className="h-3 w-3 text-slate-500 group-hover:text-slate-900 transition-colors" />
          ) : (
            <ArrowDown className="h-3 w-3 text-slate-500 group-hover:text-slate-900 transition-colors" />
          )}
        </button>
      ),
      width: "w-12",
      render: (r) => (
        <span className="text-xs font-medium text-slate-500">{r.__rowNumber}</span>
      ),
    },
    {
      key: "transaction_number",
      header: "No. Transaksi",
      render: (r) => (
        <span className="font-mono text-xs font-medium text-slate-700">
          {r.transaction_number || `#${r.id}`}
        </span>
      ),
    },
    { key: "component", header: "Unit", render: (r) => <span className="font-medium text-slate-800">{r.component?.item_name || "-"}</span> },
    { key: "officer", header: "Petugas", render: (r) => <span className="text-sm text-gray-600">{r.officer?.officer_name || "-"}</span> },
    { key: "serial", header: "SN", render: (r) => {
      // Ambil SN dari items array (dari maintenance_items)
      const sns = r.items?.filter((it) => it.serial_number).map((it) => it.serial_number) || [];
      return <span className="font-mono text-xs text-gray-500">{sns.length > 0 ? sns.join(", ") : r.component?.serial_number || "-"}</span>;
    }},
    { key: "start_date", header: "Mulai", render: (r) => formatDate(r.start_date) },
    { key: "end_date", header: "Selesai", render: (r) => r.end_date ? formatDate(r.end_date) : <span className="text-gray-400">-</span> },
    { key: "status", header: "Status", render: (r) => <span className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${MAINTENANCE_COLORS[r.status] || "bg-gray-100"}`}>{STATUS_LABELS[r.status] || r.status}</span> },
    { key: "actions", header: "Aksi", render: (r) => isAdmin ? (
      <div className="flex gap-1">
        {r.status === "In Progress" && (
          <button onClick={(e) => { e.stopPropagation(); openEdit(r); }} className="rounded-md p-1 text-blue-600 hover:bg-blue-50" title="Ubah"><Pencil className="h-4 w-4" /></button>
        )}
      </div>
    ) : null },
  ];

  const filters = [
    { label: "Unit", key: "comp", value: filterComp, onChange: (v) => { setFilterComp(v || null); setPage(1); },
      options: components.map((c) => ({ value: c.id, label: c.item_name })) },
    { label: "Status", key: "status", value: filterStatus, onChange: (v) => { setFilterStatus(v || null); setPage(1); },
      options: [{ value: "In Progress", label: "Dalam Proses" }, { value: "Completed", label: "Selesai" }, { value: "Cancelled", label: "Dibatalkan" }] },
  ];

  function openCreate() { setEditData(null); setFormOpen(true); }
  function openEdit(row) { setEditData(row); setFormOpen(true); }
  function onFormSuccess() { setFormOpen(false); setEditData(null); queryClient.invalidateQueries({ queryKey: ["maintenance"] }); }

  return (
    <div>
      <PageHeader title="Pemeliharaan" description="Riwayat pemeliharaan komponen inventaris"
        actions={isAdmin ? <button onClick={openCreate} className="flex items-center gap-1 rounded-md bg-slate-800 px-3 py-2 text-sm font-medium text-white hover:bg-slate-700"><Plus className="h-4 w-4" /> Catat Pemeliharaan</button> : null} />
      {isError && <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">Gagal memuat data.</div>}
      <div className="mb-4 flex flex-wrap items-center gap-3">
        <FilterBar filters={filters} />
        <DatePresetFilter
          startDate={startDate}
          endDate={endDate}
          onChange={(s, e) => {
            setStartDate(s);
            setEndDate(e);
            setPage(1);
          }}
        />
      </div>
      <DataTable columns={columns} data={displayedMaints} loading={isLoading} page={meta?.page} totalPages={meta?.total_pages}
        onPageChange={setPage} emptyTitle="Belum ada pemeliharaan" emptyMessage="Klik 'Catat Pemeliharaan' untuk mencatat pemeliharaan." />
      <MaintenanceForm open={formOpen} onClose={() => { setFormOpen(false); setEditData(null); }}
        editData={editData} onSuccess={onFormSuccess} />
    </div>
  );
}
