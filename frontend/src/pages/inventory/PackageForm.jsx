import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import Modal from "@/components/ui/Modal";
import { Loader2 } from "lucide-react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { inventoryApi } from "@/api/inventory";
import { useEffect } from "react";

/** Schema validasi form paket */
const packageSchema = z.object({
  box_number: z.string().min(1, "Nomor box wajib diisi").max(50, "Maksimal 50 karakter"),
  photo: z.string().max(255, "Maksimal 255 karakter").optional().or(z.literal("")),
  location: z.string().max(100, "Maksimal 100 karakter").optional().or(z.literal("")),
  notes: z.string().optional().or(z.literal("")),
});

/**
 * Form tambah/edit paket inventaris.
 *
 * @param {object} props
 * @param {boolean} props.open - Kontrol buka/tutup modal
 * @param {function} props.onClose - Callback saat modal ditutup
 * @param {object|null} props.editData - Data paket yang diedit (null = mode tambah)
 * @param {function} props.onSuccess - Callback setelah submit sukses
 */
export default function PackageForm({ open, onClose, editData, onSuccess }) {
  const queryClient = useQueryClient();
  const isEdit = !!editData;

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
    setError,
  } = useForm({
    resolver: zodResolver(packageSchema),
    defaultValues: { box_number: "", photo: "", location: "", notes: "" },
  });

  // Isi form saat edit
  useEffect(() => {
    if (editData) {
      reset({
        box_number: editData.box_number || "",
        photo: editData.photo || "",
        location: editData.location || "",
        notes: editData.notes || "",
      });
    } else {
      reset({ box_number: "", photo: "", location: "", notes: "" });
    }
  }, [editData, reset, open]);

  /** Mutation untuk create atau update */
  const mutation = useMutation({
    mutationFn: (data) =>
      isEdit
        ? inventoryApi.updatePackage(editData.id, data)
        : inventoryApi.createPackage(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["packages"] });
      onSuccess?.();
    },
    onError: (err) => {
      const msg = err.response?.data?.message;
      if (msg?.includes("sudah digunakan")) {
        setError("box_number", { message: msg });
      }
    },
  });

  /** Handler submit */
  function onSubmit(data) {
    // Bersihkan string kosong jadi undefined
    const payload = {
      ...data,
      photo: data.photo || undefined,
      location: data.location || undefined,
      notes: data.notes || undefined,
    };
    mutation.mutate(payload);
  }

  return (
    <Modal open={open} onClose={onClose} title={isEdit ? "Edit Paket" : "Tambah Paket"}>
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        {/* Box Number */}
        <div>
          <label className="mb-1 block text-sm font-medium text-gray-700">
            Nomor Box <span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            placeholder="Contoh: BOX-001"
            className={`w-full rounded-md border px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-slate-400 ${
              errors.box_number ? "border-red-400" : "border-gray-300"
            }`}
            {...register("box_number")}
          />
          {errors.box_number && (
            <p className="mt-1 text-xs text-red-500">{errors.box_number.message}</p>
          )}
        </div>

        {/* Foto URL */}
        <div>
          <label className="mb-1 block text-sm font-medium text-gray-700">
            URL Foto
          </label>
          <input
            type="text"
            placeholder="Contoh: /uploads/box001.jpg (opsional)"
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-slate-400"
            {...register("photo")}
          />
          {errors.photo && (
            <p className="mt-1 text-xs text-red-500">{errors.photo.message}</p>
          )}
        </div>

        {/* Lokasi */}
        <div>
          <label className="mb-1 block text-sm font-medium text-gray-700">
            Lokasi
          </label>
          <input
            type="text"
            placeholder="Contoh: Gudang A - Rak 3 (opsional)"
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-slate-400"
            {...register("location")}
          />
          {errors.location && (
            <p className="mt-1 text-xs text-red-500">{errors.location.message}</p>
          )}
        </div>

        {/* Catatan */}
        <div>
          <label className="mb-1 block text-sm font-medium text-gray-700">
            Catatan
          </label>
          <textarea
            rows={3}
            placeholder="Catatan tambahan (opsional)"
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-slate-400"
            {...register("notes")}
          />
        </div>

        {/* Error dari mutation */}
        {mutation.isError && !errors.box_number && (
          <div className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">
            {mutation.error?.response?.data?.message || "Gagal menyimpan data"}
          </div>
        )}

        {/* Tombol */}
        <div className="flex justify-end gap-3 pt-2">
          <button
            type="button"
            onClick={onClose}
            className="rounded-md border border-gray-300 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
          >
            Batal
          </button>
          <button
            type="submit"
            disabled={mutation.isPending}
            className="flex items-center gap-1 rounded-md bg-slate-800 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {mutation.isPending ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Menyimpan...
              </>
            ) : isEdit ? (
              "Simpan Perubahan"
            ) : (
              "Tambah Paket"
            )}
          </button>
        </div>
      </form>
    </Modal>
  );
}
