import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import Modal from "@/components/ui/Modal";
import { Loader2 } from "lucide-react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { borrowersApi } from "@/api/borrowers";
import { useEffect } from "react";

const borrowerSchema = z.object({
  borrower_type: z.enum(["Internal", "External"], { required_error: "Tipe wajib dipilih" }),
  borrower_name: z.string().min(1, "Nama wajib diisi").max(100, "Maksimal 100 karakter"),
  institution: z.string().min(1, "Instansi wajib diisi").max(150, "Maksimal 150 karakter"),
  phone: z.string().min(1, "Telepon wajib diisi").max(20).regex(/^\d+$/, "Telepon harus berupa angka"),
  nip: z.string().min(1, "NIP/NIK wajib diisi").min(16, "NIP/NIK minimal 16 digit").max(18, "NIP/NIK maksimal 18 digit").regex(/^\d+$/, "NIP/NIK harus berupa angka"),
  email: z.string().email("Email tidak valid").max(100).optional().or(z.literal("")),
  address: z.string().optional().or(z.literal("")),
  position: z.string().min(1, "Jabatan wajib diisi").max(100, "Maksimal 100 karakter"),
});

/**
 * Form tambah/edit peminjam.
 */
export default function BorrowerForm({ open, onClose, editData, onSuccess }) {
  const queryClient = useQueryClient();
  const isEdit = !!editData;

  const { register, handleSubmit, reset, formState: { errors } } = useForm({
    resolver: zodResolver(borrowerSchema),
    defaultValues: { borrower_type: "Internal", borrower_name: "", institution: "", phone: "", nip: "", email: "", address: "", position: "" },
  });

  useEffect(() => {
    if (editData) {
      reset({
        borrower_type: editData.borrower_type || "Internal",
        borrower_name: editData.borrower_name || "",
        institution: editData.institution || "",
        phone: editData.phone || "",
        nip: editData.nip || "",
        email: editData.email || "",
        address: editData.address || "",
        position: editData.position || "",
      });
    } else {
      reset({ borrower_type: "Internal", borrower_name: "", institution: "", phone: "", nip: "", email: "", address: "", position: "" });
    }
  }, [editData, reset, open]);

  const mutation = useMutation({
    mutationFn: (data) =>
      isEdit ? borrowersApi.updateBorrower(editData.id, data) : borrowersApi.createBorrower(data),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ["borrowers"] }); onSuccess?.(); },
  });

  function onSubmit(data) {
    const payload = { ...data, email: data.email || undefined, address: data.address || undefined };
    mutation.mutate(payload);
  }

  return (
    <Modal open={open} onClose={onClose} title={isEdit ? "Edit Peminjam" : "Tambah Peminjam"}>
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <div>
          <label className="mb-1 block text-sm font-medium text-gray-700">Tipe <span className="text-red-500">*</span></label>
          <select className={`w-full rounded-md border px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-slate-400 ${errors.borrower_type ? "border-red-400" : "border-gray-300"}`} {...register("borrower_type")}>
            <option value="Internal">Internal</option>
            <option value="External">Eksternal</option>
          </select>
          {errors.borrower_type && <p className="mt-1 text-xs text-red-500">{errors.borrower_type.message}</p>}
        </div>

        <div>
          <label className="mb-1 block text-sm font-medium text-gray-700">Nama Peminjam <span className="text-red-500">*</span></label>
          <input type="text" placeholder="Contoh: Doni Pratama" className={`w-full rounded-md border px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-slate-400 ${errors.borrower_name ? "border-red-400" : "border-gray-300"}`} {...register("borrower_name")} />
          {errors.borrower_name && <p className="mt-1 text-xs text-red-500">{errors.borrower_name.message}</p>}
        </div>

        <div>
          <label className="mb-1 block text-sm font-medium text-gray-700">Instansi <span className="text-red-500">*</span></label>
          <input type="text" placeholder="Contoh: BMKG Pusat"
            className={`w-full rounded-md border px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-slate-400 ${errors.institution ? "border-red-400" : "border-gray-300"}`}
            {...register("institution")} />
          {errors.institution && <p className="mt-1 text-xs text-red-500">{errors.institution.message}</p>}
        </div>

        <div>
          <label className="mb-1 block text-sm font-medium text-gray-700">Jabatan <span className="text-red-500">*</span></label>
          <input type="text" placeholder="Contoh: Kepala Seksi"
            className={`w-full rounded-md border px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-slate-400 ${errors.position ? "border-red-400" : "border-gray-300"}`}
            {...register("position")} />
          {errors.position && <p className="mt-1 text-xs text-red-500">{errors.position.message}</p>}
        </div>

        <div>
          <label className="mb-1 block text-sm font-medium text-gray-700">NIP / NIK <span className="text-red-500">*</span></label>
          <input type="text" inputMode="numeric" placeholder="Contoh: 199001012020011001"
            className={`w-full rounded-md border px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-slate-400 ${errors.nip ? "border-red-400" : "border-gray-300"}`}
            {...register("nip")} />
          {errors.nip && <p className="mt-1 text-xs text-red-500">{errors.nip.message}</p>}
        </div>

        <div>
          <label className="mb-1 block text-sm font-medium text-gray-700">Telepon <span className="text-red-500">*</span></label>
          <input type="text" inputMode="numeric" placeholder="Contoh: 081234567890"
            className={`w-full rounded-md border px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-slate-400 ${errors.phone ? "border-red-400" : "border-gray-300"}`}
            {...register("phone")} />
          {errors.phone && <p className="mt-1 text-xs text-red-500">{errors.phone.message}</p>}
        </div>

        <div>
          <label className="mb-1 block text-sm font-medium text-gray-700">Email</label>
          <input type="text" placeholder="Contoh: nama@bmkg.go.id"
            className={`w-full rounded-md border px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-slate-400 ${errors.email ? "border-red-400" : "border-gray-300"}`}
            {...register("email")} />
          {errors.email && <p className="mt-1 text-xs text-red-500">{errors.email.message}</p>}
        </div>

        <div>
          <label className="mb-1 block text-sm font-medium text-gray-700">Alamat</label>
          <textarea rows={3} placeholder="Opsional" className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-slate-400" {...register("address")} />
        </div>

        {mutation.isError && (
          <div className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{mutation.error?.response?.data?.message || "Gagal menyimpan"}</div>
        )}

        <div className="flex justify-end gap-3 pt-2">
          <button type="button" onClick={onClose} className="rounded-md border border-gray-300 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50">Batal</button>
          <button type="submit" disabled={mutation.isPending} className="flex items-center gap-1 rounded-md bg-slate-800 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-60">
            {mutation.isPending ? <><Loader2 className="h-4 w-4 animate-spin" /> Menyimpan...</> : isEdit ? "Simpan Perubahan" : "Tambah Peminjam"}
          </button>
        </div>
      </form>
    </Modal>
  );
}
