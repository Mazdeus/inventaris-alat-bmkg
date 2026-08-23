import { useState, useEffect } from "react";
import { useForm, useWatch } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import Modal from "@/components/ui/Modal";
import { Loader2, Hash, Camera, X } from "lucide-react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { inventoryApi } from "@/api/inventory";
import { uploadPhoto } from "@/api/upload";
import { MONTHS } from "@/lib/constants";

/** Schema validasi form komponen */
const componentSchema = z.object({
  item_name: z.string().min(1, "Nama unit wajib diisi").max(100, "Maksimal 100 karakter"),
  brand: z.string().min(1, "Merek wajib diisi").max(100, "Maksimal 100 karakter"),
  model: z.string().min(1, "Model wajib diisi").max(100, "Maksimal 100 karakter"),
  procurement_year: z
    .string()
    .min(1, "Tahun pengadaan wajib diisi")
    .refine((v) => /^\d{4}$/.test(v), "Format tahun tidak valid (contoh: 2024)"),
  procurement_month: z.string().min(1, "Bulan pengadaan wajib diisi"),
  supplier: z.string().max(150).optional().or(z.literal("")),
  total_quantity: z.coerce.number().min(1, "Jumlah minimal 1"),
  specifications: z.string().optional().or(z.literal("")),
  division: z.enum(["Gempa Bumi", "Tsunami", "Percepatan Tanah"], { required_error: "Divisi wajib dipilih" }),
  notes: z.string().optional().or(z.literal("")),
});

/**
 * Form tambah/edit komponen inventaris.
 */
export default function ComponentForm({ open, onClose, editData, onSuccess }) {
  const queryClient = useQueryClient();
  const isEdit = !!editData;

  const {
    register, handleSubmit, reset, control,
    formState: { errors },
  } = useForm({
    resolver: zodResolver(componentSchema),
    defaultValues: { item_name: "", brand: "", model: "",
      procurement_year: "", procurement_month: "", supplier: "", total_quantity: 1, specifications: "", division: "Gempa Bumi", notes: "" },
  });

  const watchedQuantity = useWatch({ control, name: "total_quantity" }) || 1;
  const [serialNumbers, setSerialNumbers] = useState([""]);
  const [snError, setSnError] = useState("");

  // Photo state
  const [photoFile, setPhotoFile] = useState(null);
  const [photoPreview, setPhotoPreview] = useState("");
  const [photoFullUrl, setPhotoFullUrl] = useState("");
  const [photoAbsPath, setPhotoAbsPath] = useState("");
  const [uploading, setUploading] = useState(false);

  useEffect(() => {
    if (editData) {
      reset({
        item_name: editData.item_name || "",
        brand: editData.brand || "",
        model: editData.model || "",
        procurement_year: editData.procurement_year ? String(editData.procurement_year) : "",
        procurement_month: editData.procurement_month ? String(editData.procurement_month) : "",
        supplier: editData.supplier || "",
        total_quantity: editData.total_quantity || 1,
        specifications: editData.specifications || "",
        division: editData.division || "Gempa Bumi",
        notes: editData.notes || "",
      });
      setSerialNumbers(editData.items?.map((it) => it.serial_number || "") || []);
      setPhotoFile(null);
      setPhotoPreview("");
      setPhotoFullUrl(editData.photo_url || "");
      setPhotoAbsPath(editData.photo_path || "");
    } else {
      reset({ item_name: "", brand: "", model: "",
        procurement_year: "", procurement_month: "", supplier: "", total_quantity: 1, specifications: "", division: "Gempa Bumi", notes: "" });
      setSerialNumbers([""]);
      setPhotoFile(null);
      setPhotoPreview("");
      setPhotoFullUrl("");
      setPhotoAbsPath("");
    }
  }, [editData, reset, open]);

  useEffect(() => {
    const qty = Number(watchedQuantity) || 1;
    setSerialNumbers((prev) => {
      if (prev.length === qty) return prev;
      const arr = [...prev];
      arr.length = qty;
      for (let i = 0; i < qty; i++) {
        if (arr[i] === undefined) arr[i] = "";
      }
      return arr;
    });
  }, [watchedQuantity]);

  async function handleUploadPhoto() {
    if (!photoFile) return { full_url: photoFullUrl, absolute_path: photoAbsPath };
    setUploading(true);
    try {
      const result = await uploadPhoto(photoFile);
      setPhotoFullUrl(result.full_url);
      setPhotoAbsPath(result.absolute_path);
      return result;
    } catch (err) {
      throw err;
    } finally {
      setUploading(false);
    }
  }

  const mutation = useMutation({
    mutationFn: async (data) => {
      let finalPhoto = { full_url: photoFullUrl, absolute_path: photoAbsPath };
      if (photoFile && !photoFullUrl) {
        finalPhoto = await handleUploadPhoto();
      }
      const payload = {
        ...data,
        procurement_year: data.procurement_year ? Number(data.procurement_year) : undefined,
        procurement_month: data.procurement_month ? Number(data.procurement_month) : undefined,
        photo_url: finalPhoto.full_url || undefined,
        photo_path: finalPhoto.absolute_path || undefined,
        serial_numbers: serialNumbers.map((s) => s.trim() || null),
      };
      return isEdit
        ? inventoryApi.updateComponent(editData.id, payload)
        : inventoryApi.createComponent(payload);
    },
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ["components"] }); onSuccess?.(); },
  });

  function onSubmit(data) {
    setSnError("");

    // Validasi SN: tidak boleh kosong dan tidak boleh duplikat
    const trimmedSns = serialNumbers.map((s) => s.trim());
    const emptyIndexes = [];
    const seen = new Set();
    const dupes = new Set();

    trimmedSns.forEach((sn, i) => {
      if (!sn) emptyIndexes.push(i + 1);
      else if (seen.has(sn)) dupes.add(sn);
      else seen.add(sn);
    });

    if (emptyIndexes.length > 0) {
      setSnError(`Nomor seri barang ke-${emptyIndexes.join(", ")} belum diisi.`);
      return;
    }
    if (dupes.size > 0) {
      setSnError(`Serial number duplikat: ${[...dupes].join(", ")}. Setiap SN harus unik.`);
      return;
    }

    mutation.mutate(data);
  }

  return (
    <Modal open={open} onClose={onClose} title={isEdit ? "Edit Unit" : "Tambah Unit"} maxWidth="max-w-xl">
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        {/* Nama + Merek */}
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700">Nama Unit <span className="text-red-500">*</span></label>
            <input type="text" placeholder="Contoh: Sensor Suhu" className={`w-full rounded-md border px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-slate-400 ${errors.item_name ? "border-red-400" : "border-gray-300"}`} {...register("item_name")} />
            {errors.item_name && <p className="mt-1 text-xs text-red-500">{errors.item_name.message}</p>}
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700">Merek <span className="text-red-500">*</span></label>
            <input type="text" placeholder="Contoh: Campbell" className={`w-full rounded-md border px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-slate-400 ${errors.brand ? "border-red-400" : "border-gray-300"}`} {...register("brand")} />
            {errors.brand && <p className="mt-1 text-xs text-red-500">{errors.brand.message}</p>}
          </div>
        </div>

        {/* Model */}
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700">Model <span className="text-red-500">*</span></label>
            <input type="text" placeholder="Contoh: CS215" className={`w-full rounded-md border px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-slate-400 ${errors.model ? "border-red-400" : "border-gray-300"}`} {...register("model")} />
            {errors.model && <p className="mt-1 text-xs text-red-500">{errors.model.message}</p>}
          </div>
        </div>

        {/* Spesifikasi (optional) */}
        <div>
          <label className="mb-1 block text-sm font-medium text-gray-700">Spesifikasi</label>
          <textarea rows={4} placeholder="Masukkan spesifikasi teknis komponen... (opsional)" className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-slate-400" {...register("specifications")} />
        </div>

        {/* Divisi */}
        <div>
          <label className="mb-1 block text-sm font-medium text-gray-700">Divisi <span className="text-red-500">*</span></label>
          <select className={`w-full rounded-md border px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-slate-400 ${errors.division ? "border-red-400" : "border-gray-300"}`} {...register("division")}>
            <option value="Gempa Bumi">Gempa Bumi</option>
            <option value="Tsunami">Tsunami</option>
            <option value="Percepatan Tanah">Percepatan Tanah</option>
          </select>
          {errors.division && <p className="mt-1 text-xs text-red-500">{errors.division.message}</p>}
        </div>

        {/* Tahun + Bulan Pengadaan */}
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700">Tahun Pengadaan <span className="text-red-500">*</span></label>
            <input type="text" placeholder="Contoh: 2024" maxLength={4} className={`w-full rounded-md border px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-slate-400 ${errors.procurement_year ? "border-red-400" : "border-gray-300"}`} {...register("procurement_year")} />
            {errors.procurement_year && <p className="mt-1 text-xs text-red-500">{errors.procurement_year.message}</p>}
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700">Bulan Pengadaan <span className="text-red-500">*</span></label>
            <select className={`w-full rounded-md border px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-slate-400 ${errors.procurement_month ? "border-red-400" : "border-gray-300"}`} {...register("procurement_month")}>
              <option value="">Pilih Bulan</option>
              {MONTHS.map((m, i) => (
                <option key={i + 1} value={i + 1}>{m}</option>
              ))}
            </select>
            {errors.procurement_month && <p className="mt-1 text-xs text-red-500">{errors.procurement_month.message}</p>}
          </div>
        </div>

        {/* Supplier */}
        <div>
          <label className="mb-1 block text-sm font-medium text-gray-700">Supplier</label>
          <input type="text" placeholder="Contoh: PT. Alat Sensor" className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-slate-400" {...register("supplier")} />
        </div>

        {/* Jumlah */}
        <div>
          <label className="mb-1 block text-sm font-medium text-gray-700">Jumlah Total <span className="text-red-500">*</span></label>
          <input type="number" min={1} className={`w-full rounded-md border px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-slate-400 ${errors.total_quantity ? "border-red-400" : "border-gray-300"}`} {...register("total_quantity")} />
          {errors.total_quantity && <p className="mt-1 text-xs text-red-500">{errors.total_quantity.message}</p>}
        </div>

        {/* Gambar Unit */}
        <div>
          <label className="mb-1 block text-sm font-medium text-gray-700">Gambar</label>
          <p className="mb-2 text-xs text-gray-500">Upload foto/gambar komponen (opsional).</p>
          <div className="flex flex-wrap items-start gap-4">
            <label className="inline-flex cursor-pointer items-center gap-1.5 rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-600 hover:bg-gray-50">
              <Camera className="h-4 w-4" />
              <span>{photoFile || photoFullUrl ? "Ganti Gambar" : "Pilih Gambar"}</span>
              <input type="file" accept="image/jpeg,image/png,image/webp"
                onChange={(e) => {
                  const file = e.target.files?.[0];
                  if (!file) return;
                  setPhotoFile(file);
                  setPhotoPreview(URL.createObjectURL(file));
                  setPhotoFullUrl("");
                  setPhotoAbsPath("");
                }}
                className="hidden" />
            </label>
            {(photoPreview || photoFullUrl) && (
              <div className="relative inline-block">
                <img src={photoPreview || photoFullUrl} alt="Pratinjau" className="h-24 w-24 rounded-md border border-gray-200 object-cover" />
                <button type="button" onClick={() => { setPhotoFile(null); setPhotoPreview(""); setPhotoFullUrl(""); setPhotoAbsPath(""); }}
                  className="absolute -right-1.5 -top-1.5 rounded-full bg-red-500 p-0.5 text-white hover:bg-red-600">
                  <X className="h-3 w-3" />
                </button>
              </div>
            )}
            {uploading && (
              <span className="flex items-center gap-1 text-sm text-blue-600"><Loader2 className="h-3 w-3 animate-spin" /> Mengunggah...</span>
            )}
          </div>
        </div>

        {/* Input Serial Number per barang */}
        {watchedQuantity > 0 && (
          <div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
            <h4 className="mb-3 text-sm font-semibold text-gray-700 flex items-center gap-1.5">
              <Hash className="h-4 w-4 text-gray-400" /> Nomor Seri per Barang <span className="text-red-500">*</span> ({watchedQuantity} barang)
            </h4>
            <p className="mb-3 text-xs text-gray-500">
              {isEdit
                ? "Edit serial number setiap barang. Jika quantity ditambah, isi SN untuk barang baru."
                : "Wajib diisi. Isi serial number untuk setiap barang fisik."}
            </p>
            <div className="max-h-36 overflow-y-auto rounded-md border border-gray-200 bg-white p-2">
              <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
                {serialNumbers.map((sn, idx) => (
                  <div key={idx} className="flex items-center gap-2">
                    <span className="w-6 text-xs font-medium text-gray-400 text-right">{idx + 1}.</span>
                    <input
                      type="text"
                      value={sn}
                      onChange={(e) => {
                        const updated = [...serialNumbers];
                        updated[idx] = e.target.value;
                        setSerialNumbers(updated);
                      }}
                      placeholder={`SN barang ke-${idx + 1}`}
                      className="flex-1 rounded-md border border-gray-300 px-2.5 py-1.5 text-xs outline-none focus:ring-1 focus:ring-slate-400 font-mono"
                      required={!isEdit}
                    />
                  </div>
                ))}
              </div>
            </div>
            {snError && (
              <p className="mt-2 text-xs text-red-500">{snError}</p>
            )}
          </div>
        )}

        {/* Catatan */}
        <div>
          <label className="mb-1 block text-sm font-medium text-gray-700">Catatan</label>
          <textarea rows={3} placeholder="Opsional" className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-slate-400" {...register("notes")} />
        </div>

        {mutation.isError && (
          <div className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{mutation.error?.response?.data?.message || mutation.error?.response?.data?.detail || "Gagal menyimpan data"}</div>
        )}

        <div className="flex justify-end gap-3 pt-2">
          <button type="button" onClick={onClose} className="rounded-md border border-gray-300 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50">Batal</button>
          <button type="submit" disabled={mutation.isPending} className="flex items-center gap-1 rounded-md bg-slate-800 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-60">
            {mutation.isPending ? <><Loader2 className="h-4 w-4 animate-spin" /> Menyimpan...</> : isEdit ? "Simpan Perubahan" : "Tambah Komponen"}
          </button>
        </div>
      </form>
    </Modal>
  );
}
