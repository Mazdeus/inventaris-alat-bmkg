import { useState, useEffect } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import Modal from "@/components/ui/Modal";
import StatusBadge from "@/components/ui/StatusBadge";
import { Loader2, CheckSquare, Square } from "lucide-react";
import { useMutation, useQueryClient, useQuery } from "@tanstack/react-query";
import { maintenanceApi } from "@/api/maintenance";
import { inventoryApi } from "@/api/inventory";
import { STATUS_LABELS } from "@/lib/constants";

const schema = z.object({
  inventory_component_id: z.string().min(1, "Unit wajib dipilih"),
  start_date: z.string().min(1, "Tanggal mulai wajib"),
  description: z.string().min(1, "Deskripsi wajib diisi"),
  status: z.string().min(1),
  end_date: z.string().optional().or(z.literal("")),
});

// Status yang bisa dipilih untuk perawatan
const ALLOWED_STATUSES = ["Available", "Broken"];

export default function MaintenanceForm({ open, onClose, editData, onSuccess }) {
  const queryClient = useQueryClient();
  const isEdit = !!editData;
  const [selectedCompId, setSelectedCompId] = useState(null);
  const [selectedItemIds, setSelectedItemIds] = useState([]);
  const [validationError, setValidationError] = useState("");

  const { register, handleSubmit, reset, watch, formState: { errors } } = useForm({
    resolver: zodResolver(schema),
    defaultValues: { inventory_component_id: "", start_date: new Date().toISOString().split("T")[0], description: "", status: "In Progress", end_date: "" },
  });

  const compId = watch("inventory_component_id");

  const { data: compsRes } = useQuery({
    queryKey: ["components", "all"], queryFn: () => inventoryApi.getComponents({ size: 100 }), enabled: open, staleTime: 5 * 60_000,
  });
  const components = compsRes?.data?.data || [];

  // Fetch items when component is selected
  const { data: itemsRes } = useQuery({
    queryKey: ["items", compId],
    queryFn: () => inventoryApi.getItems(Number(compId)),
    enabled: !!compId && compId !== "",
  });
  const items = itemsRes?.data?.data || [];
  // Hanya tampilkan barang yang Tersedia atau Rusak (tidak Dipinjam/sedang Perawatan)
  const selectableItems = items.filter((it) => ALLOWED_STATUSES.includes(it.status));

  useEffect(() => {
    if (editData) {
      setSelectedCompId(editData.component?.id || editData.inventory_component_id || null);
      setSelectedItemIds([]);
      // Jika ada data items dari response backend (maintenance_items), tampilkan sebagai terpilih
      if (editData.items && editData.items.length > 0) {
        setSelectedItemIds(editData.items.map((it) => it.inventory_item_id));
      }
      reset({
        inventory_component_id: String(editData.component?.id || editData.inventory_component_id || ""),
        start_date: editData.start_date?.split("T")[0] || "",
        description: editData.description || "",
        status: editData.status || "In Progress",
        end_date: editData.end_date?.split("T")[0] || "",
      });
    } else {
      setSelectedCompId(null);
      setSelectedItemIds([]);
      setValidationError("");
      reset({ inventory_component_id: "", start_date: new Date().toISOString().split("T")[0], description: "", status: "In Progress", end_date: "" });
    }
  }, [editData, reset, open]);

  function toggleItem(itemId) {
    setSelectedItemIds((prev) =>
      prev.includes(itemId) ? prev.filter((id) => id !== itemId) : [...prev, itemId]
    );
    setValidationError("");
  }

  function toggleAll() {
    if (selectedItemIds.length === selectableItems.length) {
      setSelectedItemIds([]);
    } else {
      setSelectedItemIds(selectableItems.map((it) => it.id));
    }
    setValidationError("");
  }

  const mutation = useMutation({
    mutationFn: (data) => {
      if (selectedItemIds.length === 0) {
        throw new Error("Minimal 1 barang harus dipilih");
      }
      const payload = {
        ...data,
        inventory_component_id: Number(data.inventory_component_id),
        end_date: data.end_date || undefined,
        item_ids: selectedItemIds,
      };
      return isEdit ? maintenanceApi.updateMaintenance(editData.id, payload) : maintenanceApi.createMaintenance(payload);
    },
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ["maintenance"] }); onSuccess?.(); },
    onError: (err) => {
      const msg = err?.response?.data?.detail || err?.response?.data?.message || err.message || "Gagal menyimpan";
      setValidationError(msg);
    },
  });

  function onSubmit(data) {
    setValidationError("");
    if (selectedItemIds.length === 0) {
      setValidationError("Minimal pilih 1 barang untuk perawatan");
      return;
    }
    mutation.mutate(data);
  }

  return (
    <Modal open={open} onClose={onClose} title={isEdit ? "Edit Perawatan" : "Catat Perawatan Baru"} maxWidth="max-w-xl">
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        {/* Pilih Unit */}
        <div>
          <label className="mb-1 block text-sm font-medium text-gray-700">Unit <span className="text-red-500">*</span></label>
          <select className={`w-full rounded-md border px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-slate-400 ${errors.inventory_component_id ? "border-red-400" : "border-gray-300"}`}
            {...register("inventory_component_id")} onChange={(e) => {
              register("inventory_component_id").onChange(e);
              setSelectedCompId(e.target.value ? Number(e.target.value) : null);
              setSelectedItemIds([]);
              setValidationError("");
            }}>
            <option value="">Pilih komponen...</option>
            {components.map((c) => <option key={c.id} value={c.id}>{c.item_name} ({c.brand || "-"})</option>)}
          </select>
          {errors.inventory_component_id && <p className="mt-1 text-xs text-red-500">{errors.inventory_component_id.message}</p>}
        </div>

        {/* Daftar item untuk dipilih */}
        {items.length > 0 && (
          <div className="rounded-md border border-gray-200 bg-gray-50 p-3">
            <div className="mb-2 flex items-center justify-between">
              <p className="text-xs font-medium text-gray-600">
                Pilih barang yang akan dirawat ({selectableItems.length} tersedia, minimal 1):
              </p>
              {selectableItems.length > 0 && (
                <button type="button" onClick={toggleAll} className="text-xs text-blue-600 hover:underline">
                  {selectedItemIds.length === selectableItems.length ? "Batal pilih semua" : "Pilih semua"}
                </button>
              )}
            </div>
            <div className="max-h-40 space-y-1 overflow-y-auto">
              {items.map((it, i) => {
                const isSelectable = ALLOWED_STATUSES.includes(it.status);
                const isChecked = selectedItemIds.includes(it.id);
                return (
                  <div
                    key={it.id}
                    className={`flex cursor-pointer items-center rounded px-2 py-1.5 text-xs transition ${isSelectable ? "hover:bg-slate-100" : "cursor-not-allowed opacity-50"}`}
                    onClick={() => isSelectable && toggleItem(it.id)}
                  >
                    {isSelectable ? (
                      isChecked ? <CheckSquare className="mr-2 h-4 w-4 flex-shrink-0 text-blue-600" /> : <Square className="mr-2 h-4 w-4 flex-shrink-0 text-gray-400" />
                    ) : (
                      <Square className="mr-2 h-4 w-4 flex-shrink-0 text-gray-200" />
                    )}
                    <span className="w-6 text-gray-400">#{i + 1}</span>
                    <span className="flex-1 font-mono text-gray-700">{it.serial_number || "(tanpa SN)"}</span>
                    <StatusBadge type="status" value={it.status} />
                  </div>
                );
              })}
            </div>
            {selectableItems.length === 0 && (
              <p className="text-xs text-gray-400 py-2 text-center">Tidak ada barang yang bisa dirawat. Semua barang sedang dipinjam atau dalam perawatan lain.</p>
            )}
            {selectedItemIds.length > 0 && (
              <p className="mt-2 text-xs text-blue-600">{selectedItemIds.length} barang dipilih</p>
            )}
          </div>
        )}

        {/* Tanggal + Status */}
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700">Tanggal Mulai <span className="text-red-500">*</span></label>
            <input type="date" className={`w-full rounded-md border px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-slate-400 ${errors.start_date ? "border-red-400" : "border-gray-300"}`} {...register("start_date")} />
            {errors.start_date && <p className="mt-1 text-xs text-red-500">{errors.start_date.message}</p>}
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700">Status</label>
            <select className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-slate-400" {...register("status")}>
              <option value="Scheduled">Terjadwal</option><option value="In Progress">Dalam Proses</option><option value="Completed">Selesai</option><option value="Cancelled">Dibatalkan</option>
            </select>
          </div>
        </div>
        {isEdit && (
          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700">Tanggal Selesai</label>
            <input type="date" className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-slate-400" {...register("end_date")} />
          </div>
        )}
        <div>
          <label className="mb-1 block text-sm font-medium text-gray-700">Deskripsi <span className="text-red-500">*</span></label>
          <textarea rows={3} placeholder="Deskripsikan perawatan..." className={`w-full rounded-md border px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-slate-400 ${errors.description ? "border-red-400" : "border-gray-300"}`} {...register("description")} />
          {errors.description && <p className="mt-1 text-xs text-red-500">{errors.description.message}</p>}
        </div>
        {(validationError || mutation.isError) && <div className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{validationError || mutation.error?.response?.data?.message || "Gagal menyimpan"}</div>}
        <div className="flex justify-end gap-3 pt-2">
          <button type="button" onClick={onClose} className="rounded-md border border-gray-300 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50">Batal</button>
          <button type="submit" disabled={mutation.isPending}
            className="flex items-center gap-1 rounded-md bg-slate-800 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700 disabled:opacity-60">
            {mutation.isPending ? <><Loader2 className="h-4 w-4 animate-spin" /> Menyimpan...</> : isEdit ? "Simpan Perubahan" : "Catat Perawatan"}
          </button>
        </div>
      </form>
    </Modal>
  );
}
