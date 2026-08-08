import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import Modal from "@/components/ui/Modal";
import { Loader2 } from "lucide-react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { usersApi } from "@/api/users";
import { useEffect } from "react";

const userSchema = z.object({
  username: z.string().min(3, "Minimal 3 karakter").max(50),
  password: z.string().min(6, "Minimal 6 karakter").optional().or(z.literal("")),
  full_name: z.string().min(1, "Nama wajib diisi").max(100),
  phone: z.string().min(6, "Nomor HP wajib diisi").max(20).regex(/^[0-9]+$/, "Nomor HP hanya boleh angka"),
  email: z.string().min(5, "Email wajib diisi").max(100).regex(/^[^@\s]+@[^@\s]+$/, "Format email tidak valid (harus mengandung @)"),
  is_active: z.boolean().optional(),
});

export default function UserForm({ open, onClose, editData, onSuccess }) {
  const queryClient = useQueryClient();
  const isEdit = !!editData;

  const { register, handleSubmit, reset, watch, formState: { errors } } = useForm({
    resolver: zodResolver(userSchema),
    defaultValues: { username: "", password: "", full_name: "", phone: "", email: "", is_active: true },
  });

  const isActive = watch("is_active");

  useEffect(() => {
    if (editData) {
      reset({
        username: editData.username || "",
        password: "",
        full_name: editData.full_name || "",
        phone: editData.phone || "",
        email: editData.email || "",
        is_active: editData.is_active !== false,
      });
    } else {
      reset({ username: "", password: "", full_name: "", phone: "", email: "", is_active: true });
    }
  }, [editData, reset, open]);

  const mutation = useMutation({
    mutationFn: (data) => {
      const payload = {
        full_name: data.full_name,
        phone: data.phone,
        email: data.email,
        role_id: 1,  // Selalu Admin — hanya admin yang punya akun
        is_active: data.is_active,
      };
      if (!isEdit) {
        payload.username = data.username;
        payload.password = data.password;
      }
      return isEdit ? usersApi.updateUser(editData.id, payload) : usersApi.createUser(payload);
    },
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ["users"] }); onSuccess?.(); },
  });

  function onSubmit(data) {
    const payload = { ...data };
    if (isEdit && !data.password) delete payload.password;
    mutation.mutate(payload);
  }

  return (
    <Modal open={open} onClose={onClose} title={isEdit ? "Edit Admin" : "Tambah Admin"}>
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        {!isEdit && (
          <>
            <div>
              <label className="mb-1 block text-sm font-medium text-gray-700">Username <span className="text-red-500">*</span></label>
              <input type="text" className={`w-full rounded-md border px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-slate-400 ${errors.username ? "border-red-400" : "border-gray-300"}`} {...register("username")} />
              {errors.username && <p className="mt-1 text-xs text-red-500">{errors.username.message}</p>}
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium text-gray-700">Password <span className="text-red-500">*</span></label>
              <input type="password" className={`w-full rounded-md border px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-slate-400 ${errors.password ? "border-red-400" : "border-gray-300"}`} {...register("password")} />
              {errors.password && <p className="mt-1 text-xs text-red-500">{errors.password.message}</p>}
            </div>
          </>
        )}
        {isEdit && (
          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700">Username</label>
            <input type="text" disabled value={watch("username")} className="w-full rounded-md border border-gray-200 bg-gray-50 px-3 py-2 text-sm text-gray-500 cursor-not-allowed" />
          </div>
        )}
        <div>
          <label className="mb-1 block text-sm font-medium text-gray-700">Nama Lengkap <span className="text-red-500">*</span></label>
          <input type="text" className={`w-full rounded-md border px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-slate-400 ${errors.full_name ? "border-red-400" : "border-gray-300"}`} {...register("full_name")} />
          {errors.full_name && <p className="mt-1 text-xs text-red-500">{errors.full_name.message}</p>}
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium text-gray-700">Nomor HP <span className="text-red-500">*</span></label>
          <input type="text" inputMode="numeric" placeholder="contoh: 081234567890" className={`w-full rounded-md border px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-slate-400 ${errors.phone ? "border-red-400" : "border-gray-300"}`} {...register("phone")} />
          {errors.phone && <p className="mt-1 text-xs text-red-500">{errors.phone.message}</p>}
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium text-gray-700">Email <span className="text-red-500">*</span></label>
          <input type="email" placeholder="contoh: admin@bmkg.go.id" className={`w-full rounded-md border px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-slate-400 ${errors.email ? "border-red-400" : "border-gray-300"}`} {...register("email")} />
          {errors.email && <p className="mt-1 text-xs text-red-500">{errors.email.message}</p>}
        </div>
        {isEdit && (
          <div className="flex items-center gap-2">
            <input type="checkbox" id="is_active" className="h-4 w-4 rounded border-gray-300" {...register("is_active")} />
            <label htmlFor="is_active" className="text-sm text-gray-700">Akun Aktif</label>
          </div>
        )}
        {mutation.isError && <div className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{mutation.error?.response?.data?.message || "Gagal menyimpan"}</div>}
        <div className="flex justify-end gap-3 pt-2">
          <button type="button" onClick={onClose} className="rounded-md border border-gray-300 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50">Batal</button>
          <button type="submit" disabled={mutation.isPending} className="flex items-center gap-1 rounded-md bg-slate-800 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700 disabled:opacity-60">
            {mutation.isPending ? <><Loader2 className="h-4 w-4 animate-spin" /> Menyimpan...</> : isEdit ? "Simpan" : "Tambah"}
          </button>
        </div>
      </form>
    </Modal>
  );
}
