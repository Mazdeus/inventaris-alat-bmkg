import { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { inventoryApi } from "@/api/inventory";
import { useAuth } from "@/contexts/AuthContext";
import PageHeader from "@/components/ui/PageHeader";
import StatusBadge from "@/components/ui/StatusBadge";
import { ConfirmDialog } from "@/components/ui/ConfirmDialog";
import ItemStatusTimeline from "@/components/ItemStatusTimeline";
import { STATUS_LABELS } from "@/lib/constants";
import { ArrowLeft, Calendar, Tag, Wrench, Hash, Layers, Trash2, RefreshCw, Clock } from "lucide-react";
import { toast } from "sonner";

// Status ID mapping (dari seed: Available=1, Broken=4)
const STATUS_IDS = { Available: 1, Broken: 4 };
const TOGGLE_MAP = { Available: 4, Broken: 1 };

/**
 * Halaman detail satu komponen inventaris.
 * Route: /inventory/components/:id
 */
export default function ComponentDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { isAdmin } = useAuth();
  const [deleteItem, setDeleteItem] = useState(null);
  const [togglingItem, setTogglingItem] = useState(null);
  const [historyItem, setHistoryItem] = useState(null);

  const { data, isLoading, isError } = useQuery({
    queryKey: ["component", id],
    queryFn: () => inventoryApi.getComponent(Number(id)),
    enabled: !!id,
  });

  // Fetch items
  const { data: itemsRes } = useQuery({
    queryKey: ["items", id],
    queryFn: () => inventoryApi.getItems(Number(id)),
    enabled: !!id,
  });

  const comp = data?.data?.data;
  const items = itemsRes?.data?.data || [];

  // Delete item mutation
  const deleteMutation = useMutation({
    mutationFn: (itemId) => inventoryApi.deleteItem(itemId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["items", id] });
      queryClient.invalidateQueries({ queryKey: ["component", id] });
      queryClient.invalidateQueries({ queryKey: ["components"] });
      setDeleteItem(null);
    },
  });

  // Toggle status item (Available ↔ Broken)
  const toggleStatusMutation = useMutation({
    mutationFn: (item) => {
      const newStatusId = TOGGLE_MAP[item.status];
      return inventoryApi.updateItem(item.id, { status_id: newStatusId });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["items", id] });
      queryClient.invalidateQueries({ queryKey: ["component", id] });
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

  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="h-6 w-32 animate-pulse rounded bg-gray-200" />
        <div className="h-48 animate-pulse rounded-lg bg-gray-200" />
      </div>
    );
  }

  if (isError || !comp) {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 p-6 text-center text-red-700">
        Gagal memuat data komponen.
        <button onClick={() => navigate("/inventory/components")} className="mt-2 block text-sm underline">Kembali ke daftar</button>
      </div>
    );
  }

  const avail = comp.available_quantity ?? 0;
  const total = comp.total_quantity ?? 0;

  // Hitung per-status dari items (lebih akurat)
  const availableCount = items.filter((it) => it.status === "Available").length;
  const borrowedCount = items.filter((it) => it.status === "Borrowed").length;
  const maintenanceCount = items.filter((it) => it.status === "Maintenance").length;
  const brokenCount = items.filter((it) => it.status === "Broken").length;

  return (
    <div>
      <button onClick={() => navigate(-1)} className="mb-4 flex items-center gap-1 text-sm text-gray-500 hover:text-slate-700">
        <ArrowLeft className="h-4 w-4" /> Kembali
      </button>

      <PageHeader title={comp.item_name} description={`Detail komponen inventaris`} />

      {/* Info grid */}
      <div className="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <InfoCard icon={Tag} label="Merek / Model" value={[comp.brand, comp.model].filter(Boolean).join(" / ") || "-"} />
        <InfoCard icon={Calendar} label="Supplier" value={comp.supplier || "-"} />
        <InfoCard icon={Wrench} label="Tahun Pengadaan" value={comp.procurement_year ? String(comp.procurement_year) : "-"} />
        <InfoCard icon={Hash} label="Nomor Seri" value={comp.serial_number || "-"} />
        <InfoCard icon={Layers} label="Divisi" value={comp.division || "-"} />
      </div>

      {/* Stok card */}
      <div className="mb-6 rounded-lg border border-gray-200 bg-white p-5">
        <h3 className="mb-3 text-sm font-semibold text-gray-700">Informasi Stok</h3>
        <div className="flex flex-wrap items-center gap-6">
          <div>
            <p className="text-xs text-gray-500">Total</p>
            <p className="text-2xl font-bold text-slate-800">{total}</p>
          </div>
          <div>
            <p className="text-xs text-gray-500">Tersedia</p>
            <p className={`text-2xl font-bold ${availableCount > 0 ? "text-emerald-600" : "text-red-500"}`}>{availableCount}</p>
          </div>
          <div>
            <p className="text-xs text-gray-500">Dipinjam</p>
            <p className="text-2xl font-bold text-orange-600">{borrowedCount}</p>
          </div>
          <div>
            <p className="text-xs text-gray-500">Rusak</p>
            <p className="text-2xl font-bold text-red-500">{brokenCount}</p>
          </div>
          <div>
            <p className="text-xs text-gray-500">Perbaikan</p>
            <p className="text-2xl font-bold text-blue-600">{maintenanceCount}</p>
          </div>
        </div>
      </div>

      {/* Detail info */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div className="rounded-lg border border-gray-200 bg-white p-4">
          <p className="mb-1 text-xs font-medium uppercase text-gray-500">Supplier</p>
          <p className="text-sm text-slate-700">{comp.supplier || "-"}</p>
        </div>
      </div>

      {/* Spesifikasi */}
      {comp.specifications && (
        <div className="mt-4 rounded-lg border border-gray-200 bg-white p-4">
          <p className="mb-1 text-xs font-medium uppercase text-gray-500">Spesifikasi</p>
          <p className="whitespace-pre-wrap text-sm text-gray-700">{comp.specifications}</p>
        </div>
      )}

      {/* Gambar Komponen */}
      {comp.photo_url && (
        <div className="mt-4 rounded-lg border border-gray-200 bg-white p-4">
          <p className="mb-2 text-xs font-medium uppercase text-gray-500">Gambar Unit</p>
          <img
            src={comp.photo_url}
            alt={comp.item_name}
            className="max-h-80 rounded-md object-contain"
            onError={(e) => { e.target.style.display = "none"; }}
          />
        </div>
      )}

      {comp.notes && (
        <div className="mt-4 rounded-lg border border-gray-200 bg-white p-4">
          <p className="mb-1 text-xs font-medium uppercase text-gray-500">Catatan</p>
          <p className="text-sm text-gray-700">{comp.notes}</p>
        </div>
      )}

      {/* Konfirmasi hapus item */}
      <ConfirmDialog
        open={!!deleteItem}
        onOpenChange={() => setDeleteItem(null)}
        title="Hapus Item"
        message={`Anda akan menghapus item ${deleteItem?.serial_number || "-"} dengan status ${STATUS_LABELS[deleteItem?.status] || deleteItem?.status}. Status item akan diubah menjadi "Dihapuskan" dan total quantity unit akan berkurang.`}
        onConfirm={() => deleteItem && deleteMutation.mutate(deleteItem.id)}
        confirmLabel="Hapus"
        variant="danger"
      />

      {/* Daftar Item (per barang fisik) */}
      {items.length > 0 && (
        <div className="mt-6 rounded-lg border border-gray-200 bg-white">
          <div className="border-b border-gray-100 px-4 py-3">
            <h3 className="text-sm font-semibold text-gray-700">
              Daftar Barang Individual ({items.length} barang)
            </h3>
            <p className="text-xs text-gray-400 mt-0.5">
              Admin dapat mengubah status barang antara Tersedia dan Rusak melalui tombol di kolom Aksi.
            </p>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-100 bg-gray-50 text-left">
                  <th className="px-4 py-2 font-semibold text-gray-600 w-16">#</th>
                  <th className="px-4 py-2 font-semibold text-gray-600">Nomor Seri</th>
                  <th className="px-4 py-2 font-semibold text-gray-600">Status</th>
                  {isAdmin && <th className="px-4 py-2 font-semibold text-gray-600 w-24">Aksi</th>}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {items.map((item, idx) => {
                  const canDelete = item.status === "Available" || item.status === "Broken";
                  const canToggle = TOGGLE_MAP[item.status] !== undefined;
                  const isToggling = togglingItem === item.id;
                  return (
                  <tr key={item.id} className="hover:bg-slate-50">
                    <td className="px-4 py-2 text-gray-500">{idx + 1}</td>
                    <td className="px-4 py-2">
                      <span className={`font-mono text-xs ${item.serial_number ? "text-slate-700" : "text-gray-400 italic"}`}>
                        {item.serial_number || "Belum diisi"}
                      </span>
                    </td>
                    <td className="px-4 py-2">
                      <StatusBadge type="status" value={item.status} />
                    </td>
                    {isAdmin && (
                      <td className="px-4 py-2">
                        <div className="flex items-center gap-1">
                          {/* Tombol toggle status */}
                          <button
                            onClick={() => handleToggleStatus(item)}
                            disabled={!canToggle || isToggling}
                            title={canToggle
                              ? `Ubah ke ${STATUS_LABELS[TOGGLE_MAP[item.status] === STATUS_IDS.Available ? "Available" : "Broken"]}`
                              : "Status tidak bisa diubah manual"}
                            className="rounded-md p-1 text-blue-600 hover:bg-blue-50 disabled:cursor-not-allowed disabled:opacity-30"
                          >
                            <RefreshCw className={`h-4 w-4 ${isToggling ? "animate-spin" : ""}`} />
                          </button>
                          {/* Tombol hapus */}
                          <button
                            onClick={() => setDeleteItem(item)}
                            disabled={!canDelete}
                            title={canDelete ? "Hapus item" : "Item tidak bisa dihapus (hanya Tersedia & Rusak)"}
                            className="rounded-md p-1 text-red-600 hover:bg-red-50 disabled:cursor-not-allowed disabled:opacity-30"
                          >
                            <Trash2 className="h-4 w-4" />
                          </button>
                          {/* Tombol riwayat */}
                          <button
                            onClick={(e) => { e.stopPropagation(); handleShowHistory(item); }}
                            className="rounded-md p-1 text-gray-500 hover:bg-gray-100"
                            title="Lihat riwayat status"
                          >
                            <Clock className="h-4 w-4" />
                          </button>
                        </div>
                      </td>
                    )}
                  </tr>
                )})}
              </tbody>
            </table>
          </div>
        </div>
      )}

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

/** Kartu info kecil dalam grid */
function InfoCard({ icon: Icon, label, value, onClick }) {
  return (
    <div className={`rounded-lg border border-gray-200 bg-white p-4 ${onClick ? "cursor-pointer hover:border-blue-300 hover:shadow-sm" : ""}`} onClick={onClick}>
      <div className="mb-2 flex items-center gap-2">
        <Icon className="h-4 w-4 text-gray-400" />
        <p className="text-xs font-medium uppercase text-gray-500">{label}</p>
      </div>
      <p className="text-sm font-medium text-slate-700">{value}</p>
    </div>
  );
}
