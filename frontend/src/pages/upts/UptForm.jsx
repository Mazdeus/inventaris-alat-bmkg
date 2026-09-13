import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Loader2 } from "lucide-react";
import Modal from "@/components/ui/Modal";
import { uptsApi } from "@/api/upts";

const uptSchema = z.object({
  name: z.string().min(1, "Nama UPT wajib diisi").max(150, "Maksimal 150 karakter"),
  address: z.string().optional().or(z.literal("")),
  phone: z.string().max(50, "Maksimal 50 karakter").optional().or(z.literal("")),
});

/**
 * Modal form Tambah/Edit data UPT.
 */
export default function UptForm({ open, onClose, editData, onSuccess }) {
  const queryClient = useQueryClient();
  const isEdit = !!editData;

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm({
    resolver: zodResolver(uptSchema),
    defaultValues: {
      name: "",
      address: "",
      phone: "",
    },
  });

  useEffect(() => {
    if (editData) {
      reset({
        name: editData.name || "",
        address: editData.address || "",
        phone: editData.phone || "",
      });
    } else {
      reset({
        name: "",
        address: "",
        phone: "",
      });
    }
  }, [editData, reset, open]);

  const mutation = useMutation({
    mutationFn: (data) =>
      isEdit ? uptsApi.updateUpt(editData.id, data) : uptsApi.createUpt(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["upts"] });
      toast.success(isEdit ? "Data UPT berhasil diperbarui" : "Data UPT berhasil ditambahkan");
      onSuccess?.();
      onClose();
    },
    onError: (err) => {
      toast.error(err?.response?.data?.detail || "Gagal menyimpan data UPT");
    },
  });

  function onSubmit(data) {
    const payload = {
      name: data.name.trim(),
      address: data.address?.trim() || undefined,
      phone: data.phone?.trim() || undefined,
    };
    mutation.mutate(payload);
  }

  return (
    <Modal
      open={open}
      onClose={onClose}
      title={isEdit ? "Edit UPT" : "Tambah UPT"}
    >
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <div>
          <label className="mb-1 block text-sm font-medium text-gray-700">
            Nama UPT <span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            placeholder="contoh: Stasiun Geofisika Klas I Bandung"
            {...register("name")}
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm outline-none transition focus:border-slate-500 focus:ring-1 focus:ring-slate-500"
          />
          {errors.name && (
            <p className="mt-1 text-xs text-red-500">{errors.name.message}</p>
          )}
        </div>

        <div>
          <label className="mb-1 block text-sm font-medium text-gray-700">
            Alamat <span className="text-xs text-gray-400 font-normal">(Opsional)</span>
          </label>
          <textarea
            rows={3}
            placeholder="contoh: Jl. Cemara No. 66, Pasteur, Sukajadi, Kota Bandung"
            {...register("address")}
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm outline-none transition focus:border-slate-500 focus:ring-1 focus:ring-slate-500"
          />
          {errors.address && (
            <p className="mt-1 text-xs text-red-500">{errors.address.message}</p>
          )}
        </div>

        <div>
          <label className="mb-1 block text-sm font-medium text-gray-700">
            Kontak / Telepon <span className="text-xs text-gray-400 font-normal">(Opsional)</span>
          </label>
          <input
            type="text"
            placeholder="contoh: (022) 2038794 atau kontak narahubung"
            {...register("phone")}
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm outline-none transition focus:border-slate-500 focus:ring-1 focus:ring-slate-500"
          />
          {errors.phone && (
            <p className="mt-1 text-xs text-red-500">{errors.phone.message}</p>
          )}
        </div>

        <div className="flex justify-end gap-2 pt-2">
          <button
            type="button"
            onClick={onClose}
            className="rounded-md border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 transition"
          >
            Batal
          </button>
          <button
            type="submit"
            disabled={mutation.isPending}
            className="flex items-center gap-1.5 rounded-md bg-slate-800 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700 disabled:opacity-50 transition"
          >
            {mutation.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
            {isEdit ? "Simpan Perubahan" : "Simpan UPT"}
          </button>
        </div>
      </form>
    </Modal>
  );
}
