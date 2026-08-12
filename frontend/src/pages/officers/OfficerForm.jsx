import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import Modal from "@/components/ui/Modal";
import { Loader2 } from "lucide-react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { officersApi } from "@/api/officers";
import { useEffect } from "react";

const officerSchema = z.object({
  officer_name: z.string().min(1, "Nama wajib diisi").max(100, "Maksimal 100 karakter"),
  nip: z.string().min(1, "NIP wajib diisi").length(18, "NIP harus 18 digit").regex(/^\d+$/, "NIP harus berupa angka"),
  phone: z.string().max(20).regex(/^\d+$/, "Telepon harus berupa angka").optional().or(z.literal("")),
  email: z.string().email("Email tidak valid").max(100).optional().or(z.literal("")),
  position: z.string().max(100).optional().or(z.literal("")),
  is_active: z.boolean().optional(),
});

/**
 * Form tambah/edit petugas.
 */
export default function OfficerForm({ open, onClose, editData, onSuccess }) {
  const queryClient = useQueryClient();
  const isEdit = !!editData;

  const {
    register,
    handleSubmit,
    reset,
    watch,
    formState: { errors },
  } = useForm({
    resolver: zodResolver(officerSchema),
    defaultValues: {
      officer_name: "",
      nip: "",
      phone: "",
      email: "",
      position: "",
      is_active: true,
    },
  });

  useEffect(() => {
    if (editData) {
      reset({
        officer_name: editData.officer_name || "",
        nip: editData.nip || "",
        phone: editData.phone || "",
        email: editData.email || "",
        position: editData.position || "",
        is_active: editData.is_active !== false,
      });
    } else {
      reset({
        officer_name: "",
        nip: "",
        phone: "",
        email: "",
        position: "",
        is_active: true,
      });
    }
  }, [editData, reset, open]);

  const mutation = useMutation({
    mutationFn: (data) =>
      isEdit
        ? officersApi.updateOfficer(editData.id, data)
        : officersApi.createOfficer(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["officers"] });
      onSuccess?.();
    },
  });

  function onSubmit(data) {
    const payload = {
      ...data,
      phone: data.phone || undefined,
      email: data.email || undefined,
      position: data.position || undefined,
    };
    mutation.mutate(payload);
  }

  return (
    <Modal
      open={open}
      onClose={onClose}
      title={isEdit ? "Edit Petugas" : "Tambah Petugas"}
    >
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <div>
          <label className="mb-1 block text-sm font-medium text-gray-700">
            Nama Petugas <span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            placeholder="Contoh: Ahmad Fauzi"
            className={`w-full rounded-md border px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-slate-400 ${
              errors.officer_name ? "border-red-400" : "border-gray-300"
            }`}
            {...register("officer_name")}
          />
          {errors.officer_name && (
            <p className="mt-1 text-xs text-red-500">{errors.officer_name.message}</p>
          )}
        </div>

        <div>
          <label className="mb-1 block text-sm font-medium text-gray-700">
            NIP <span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            inputMode="numeric"
            placeholder="Contoh: 199001012020011001"
            className={`w-full rounded-md border px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-slate-400 font-mono ${
              errors.nip ? "border-red-400" : "border-gray-300"
            }`}
            {...register("nip")}
          />
          {errors.nip && (
            <p className="mt-1 text-xs text-red-500">{errors.nip.message}</p>
          )}
        </div>

        <div>
          <label className="mb-1 block text-sm font-medium text-gray-700">Jabatan</label>
          <input
            type="text"
            placeholder="Contoh: Teknisi"
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-slate-400"
            {...register("position")}
          />
        </div>

        <div>
          <label className="mb-1 block text-sm font-medium text-gray-700">Telepon</label>
          <input
            type="text"
            inputMode="numeric"
            placeholder="Contoh: 081234567890"
            className={`w-full rounded-md border px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-slate-400 ${
              errors.phone ? "border-red-400" : "border-gray-300"
            }`}
            {...register("phone")}
          />
          {errors.phone && (
            <p className="mt-1 text-xs text-red-500">{errors.phone.message}</p>
          )}
        </div>

        <div>
          <label className="mb-1 block text-sm font-medium text-gray-700">Email</label>
          <input
            type="text"
            placeholder="Contoh: ahmad@bmkg.go.id"
            className={`w-full rounded-md border px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-slate-400 ${
              errors.email ? "border-red-400" : "border-gray-300"
            }`}
            {...register("email")}
          />
          {errors.email && (
            <p className="mt-1 text-xs text-red-500">{errors.email.message}</p>
          )}
        </div>

        {isEdit && (
          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="is_active"
              className="h-4 w-4 rounded border-gray-300 text-slate-800 focus:ring-slate-400"
              {...register("is_active")}
            />
            <label htmlFor="is_active" className="text-sm text-gray-700">
              Aktif
            </label>
          </div>
        )}

        {mutation.isError && (
          <div className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">
            {mutation.error?.response?.data?.message || "Gagal menyimpan"}
          </div>
        )}

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
                <Loader2 className="h-4 w-4 animate-spin" /> Menyimpan...
              </>
            ) : isEdit ? (
              "Simpan Perubahan"
            ) : (
              "Tambah Petugas"
            )}
          </button>
        </div>
      </form>
    </Modal>
  );
}
