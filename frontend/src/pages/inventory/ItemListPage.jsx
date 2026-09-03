import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { inventoryApi } from "@/api/inventory";
import { useAuth } from "@/contexts/AuthContext";
import DataTable from "@/components/ui/DataTable";
import PageHeader from "@/components/ui/PageHeader";
import FilterBar from "@/components/ui/FilterBar";
import StatusBadge from "@/components/ui/StatusBadge";
import { ConfirmDialog } from "@/components/ui/ConfirmDialog";
import ItemStatusTimeline from "@/components/ItemStatusTimeline";
import { STATUS_LABELS } from "@/lib/constants";
import { RefreshCw, Trash2, Clock } from "lucide-react";
import { toast } from "sonner";

// Status ID mapping
const STATUS_IDS = { Available: 1, Broken: 4 };
const TOGGLE_MAP = { Available: 4, Broken: 1 };

/**
 * Halaman daftar barang individual (lintas unit). Admin dapat mengubah status & menghapus.
 */
export default function ItemListPage() {
  const queryClient = useQueryClient();
  const { isAdmin } = useAuth();

  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [filterStatus, setFilterStatus] = useState(null);
  const [filterComponent, setFilterComponent] = useState(null);
  const [deleteItem, setDeleteItem] = useState(null);
  const [togglingItem, setTogglingItem] = useState(null);
  const [historyItem, setHistoryItem] = useState(null);

  // Fetch items
  const { data, isLoading, isError } = useQuery({
    queryKey: ["all-items", page, search, filterStatus, filterComponent],
    queryFn: () =>
      inventoryApi.getAllItems({
        page,
        size: 10,
        search: search || undefined,
        status_id: filterStatus || undefined,
        component_id: filterComponent || undefined,
      }),
    keepPreviousData: true,
  });

  // Fetch statuses untuk dropdown filter
  const { data: statusesRes } = useQuery({
    queryKey: ["statuses"],
    queryFn: () => inventoryApi.getStatuses(),
    staleTime: 5 * 60_000,
  });

  // Fetch components untuk dropdown filter unit
  const { data: compsRes } = useQuery({
    queryKey: ["components-all"],
    queryFn: () => inventoryApi.getComponents({ size: 200 }),
    staleTime: 5 * 60_000,
  });

  const items = data?.data?.data || [];
  const meta = data?.data?.meta;
  const statuses = statusesRes?.data?.data || [];
  const components = compsRes?.data?.data || [];

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: (itemId) => inventoryApi.deleteItem(itemId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["all-items"] });
      queryClient.invalidateQueries({ queryKey: ["components"] });
      setDeleteItem(null);
    },
    onError: (err) => {
      toast.error(err?.response?.data?.detail || "Gagal menghapus barang");
    },
  });

  // Toggle status
  const toggleStatusMutation = useMutation({
    mutationFn: (item) => {
      const newStatusId = TOGGLE_MAP[item.status];
      return inventoryApi.updateItem(item.id, { status_id: newStatusId });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["all-items"] });
      queryClient.invalidateQueries({ queryKey: ["components"] });
      setTogglingItem(null);
    },
    onError: (err) => {
      setTogglingItem(null);
      toast.error(err?.response?.data?.detail || "Gagal mengubah status barang");
    },
  });

  function handleToggleStatus(item) {
    setTogglingItem(item.id);
    toggleStatusMutation.mutate(item);
  }

  function handleShowHistory(item) {
    setHistoryItem({ item, data: null, loading: true });
    inventoryApi.getItemHistory(item.id).then((res) => {
      setHistoryItem((prev) => prev && { ...prev, data: res.data?.data || [], loading: false });
    }).catch(() => {
      setHistoryItem((prev) => prev && { ...prev, data: [], loading: false, error: true });
    });
  }

  const columns = [
    {
      key: "serial_number",
      header: "Nomor Seri",
      render: (row) => (
        <span className={`font-mono text-xs ${row.serial_number ? "text-slate-700" : "text-gray-400 italic"}`}>
          {row.serial_number || "Belum diisi"}
        </span>
      ),
    },
    {
      key: "component_name",
      header: "Unit",
      render: (row) => (
        <div>
          <p className="text-sm font-medium text-slate-700">{row.component_name}</p>
          {row.brand && <p className="text-xs text-gray-400">{row.brand}</p>}
        </div>
      ),
    },
    {
      key: "division",
      header: "Divisi",
      render: (row) => (
        <span className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${
          row.division === "Gempa Bumi" ? "bg-yellow-100 text-yellow-800" :
          row.division === "Tsunami" ? "bg-blue-100 text-blue-800" :
          row.division === "Percepatan Tanah" ? "bg-emerald-100 text-emerald-800" :
          "bg-gray-100 text-gray-600"
        }`}>{row.division || "-"}</span>
      ),
    },
    {
      key: "status",
      header: "Status",
      render: (row) => <StatusBadge type="status" value={row.status} />,
    },
    {
      key: "actions",
      header: "Aksi",
      render: (row) =>
        isAdmin ? (
          <div className="flex items-center gap-1">
            <button
              onClick={(e) => { e.stopPropagation(); handleToggleStatus(row); }}
              disabled={!(TOGGLE_MAP[row.status] !== undefined) || togglingItem === row.id}
              title={TOGGLE_MAP[row.status] !== undefined
                ? `Ubah ke ${STATUS_LABELS[TOGGLE_MAP[row.status] === STATUS_IDS.Available ? "Available" : "Broken"]}`
                : "Status tidak bisa diubah manual"}
              className="rounded-md p-1 text-blue-600 hover:bg-blue-50 disabled:cursor-not-allowed disabled:opacity-30"
            >
              <RefreshCw className={`h-4 w-4 ${togglingItem === row.id ? "animate-spin" : ""}`} />
            </button>
            <button
              onClick={(e) => { e.stopPropagation(); setDeleteItem(row); }}
              disabled={!(row.status === "Available" || row.status === "Broken")}
              title={row.status === "Available" || row.status === "Broken" ? "Hapus barang" : "Hanya barang Tersedia & Rusak yang bisa dihapus"}
              className="rounded-md p-1 text-red-600 hover:bg-red-50 disabled:cursor-not-allowed disabled:opacity-30"
            >
              <Trash2 className="h-4 w-4" />
            </button>
            <button
              onClick={(e) => { e.stopPropagation(); handleShowHistory(row); }}
              className="rounded-md p-1 text-gray-500 hover:bg-gray-100"
              title="Lihat riwayat status"
            >
              <Clock className="h-4 w-4" />
            </button>
          </div>
        ) : null,
    },
  ];

  const filters = [
    {
      label: "Status",
      key: "status",
      value: filterStatus,
      onChange: (v) => { setFilterStatus(v || null); setPage(1); },
      options: statuses.filter((s) => s.status_name !== "Deleted").map((s) => ({ value: s.id, label: STATUS_LABELS[s.status_name] || s.status_name })),
    },
    {
      label: "Unit",
      key: "component",
      value: filterComponent,
      onChange: (v) => { setFilterComponent(v || null); setPage(1); },
      options: components.map((c) => ({ value: c.id, label: c.item_name })),
    },
  ];

  return (
    <div>
      <PageHeader
        title="Daftar Barang"
        description="Lihat semua barang individual berdasarkan status, unit, atau nomor seri"
      />

      {isError && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          Gagal memuat data. Pastikan backend berjalan.
        </div>
      )}

      <FilterBar filters={filters} />

      <DataTable
        columns={columns}
        data={items}
        loading={isLoading}
        page={meta?.page}
        totalPages={meta?.total_pages}
        onPageChange={setPage}
        searchValue={search}
        onSearchChange={(v) => { setSearch(v); setPage(1); }}
        searchPlaceholder="Cari nomor seri..."
        emptyTitle="Belum ada barang"
        emptyMessage="Tambahkan unit inventaris dengan total quantity > 0 untuk melihat barang individual di sini."
      />

      {/* Konfirmasi hapus item */}
      <ConfirmDialog
        open={!!deleteItem}
        onOpenChange={() => setDeleteItem(null)}
        title="Hapus Barang"
        message={`Anda akan menghapus barang ${deleteItem?.serial_number || "-"} (${deleteItem?.component_name || ""}) dengan status ${STATUS_LABELS[deleteItem?.status] || deleteItem?.status}. Status barang akan diubah menjadi "Dihapuskan".`}
        onConfirm={() => deleteItem && deleteMutation.mutate(deleteItem.id)}
        confirmLabel="Hapus"
        variant="danger"
        requirePassword
      />

      {/* Modal Riwayat Status */}
      {historyItem && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40"
          onClick={() => setHistoryItem(null)}>
          <div className="w-full max-w-md max-h-[70vh] overflow-y-auto rounded-lg bg-white p-5 shadow-xl"
            onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-semibold text-gray-800">
                Riwayat Status: {historyItem.item.serial_number || `#${historyItem.item.id}`}
              </h3>
              <button onClick={() => setHistoryItem(null)}
                className="text-gray-400 hover:text-gray-600 text-lg leading-none">&times;</button>
            </div>
            <ItemStatusTimeline
              history={historyItem.data || []}
              loading={historyItem.loading}
              error={historyItem.error}
            />
          </div>
        </div>
      )}
    </div>
  );
}
