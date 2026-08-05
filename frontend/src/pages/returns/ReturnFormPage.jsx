import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { returnsApi } from "@/api/returns";
import { borrowApi } from "@/api/borrow";
import { officersApi } from "@/api/officers";
import { uploadPhoto } from "@/api/upload";
import PageHeader from "@/components/ui/PageHeader";
import { ArrowLeft, Loader2, Camera, X, FileDown, FileUp } from "lucide-react";

export default function ReturnFormPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [borrowId, setBorrowId] = useState("");
  const [returnDate, setReturnDate] = useState(new Date().toISOString().split("T")[0]);
  const [officerId, setOfficerId] = useState("");
  const [details, setDetails] = useState([]);
  // details: [{ inventory_component_id, item_name, items: [{inventory_item_id, serial_number, condition, notes}] }]
  const [serverError, setServerError] = useState("");
  const [photoFile, setPhotoFile] = useState(null);
  const [photoPreview, setPhotoPreview] = useState("");
  const [photoUrl, setPhotoUrl] = useState("");
  const [uploading, setUploading] = useState(false);
  const [lateReason, setLateReason] = useState("");

  // Fetch borrowed transactions
  const { data: txRes } = useQuery({
    queryKey: ["transactions", "active"],
    queryFn: () => borrowApi.getTransactions({ size: 100, status: "Dipinjam" }),
  });
  const activeTxs = txRes?.data?.data || [];

  // Fetch officers
  const { data: officersRes } = useQuery({
    queryKey: ["officers", "active"],
    queryFn: () => officersApi.getOfficers({ size: 100, is_active: true }),
    staleTime: 2 * 60_000,
  });
  const officers = officersRes?.data?.data || [];

  // Fetch selected transaction detail
  const { data: detailRes } = useQuery({
    queryKey: ["transaction", borrowId],
    queryFn: () => borrowApi.getTransaction(Number(borrowId)),
    enabled: !!borrowId,
  });

  const selectedTx = detailRes?.data?.data;

  // When transaction is selected, populate details per SN
  function handleSelectTx(id) {
    setBorrowId(id);
    setDetails([]);
    setServerError("");
    setLateReason("");
  }

  // Populate details when transaction detail arrives — per SN
  useEffect(() => {
    if (selectedTx?.details && borrowId) {
      const mapped = [];
      for (const d of selectedTx.details) {
        const items = (d.selected_items || []).map((it) => ({
          inventory_item_id: it.id,
          serial_number: it.serial_number || `#${it.id}`,
          condition: "Baik",
          notes: "",
        }));
        if (items.length > 0) {
          mapped.push({
            inventory_component_id: d.component?.id || d.inventory_component_id,
            item_name: d.component?.item_name || "-",
            items,
          });
        }
      }
      setDetails(mapped);
    }
  }, [selectedTx, borrowId]);

  // Is return late?
  const isLate = selectedTx && returnDate > selectedTx.expected_return_date;
  const daysLate = isLate
    ? Math.ceil((new Date(returnDate) - new Date(selectedTx.expected_return_date)) / (1000 * 60 * 60 * 24))
    : 0;

  function updateItemCondition(compIdx, itemIdx, field, value) {
    setDetails((prev) => {
      const updated = [...prev];
      const items = [...updated[compIdx].items];
      items[itemIdx] = { ...items[itemIdx], [field]: value };
      updated[compIdx] = { ...updated[compIdx], items };
      return updated;
    });
  }

  const mutation = useMutation({
    mutationFn: ({ photo_url }) =>
      returnsApi.createReturn({
        borrow_id: Number(borrowId),
        received_by: officerId ? Number(officerId) : undefined,
        return_date: returnDate,
        photo: photo_url,
        late_reason: isLate ? lateReason : undefined,
        details: details.map((d) => ({
          inventory_component_id: d.inventory_component_id,
          items: d.items.map((it) => ({
            inventory_item_id: it.inventory_item_id,
            condition: it.condition,
            notes: it.notes || undefined,
          })),
        })),
      }),
    onSuccess: (res) => {
      queryClient.invalidateQueries({ queryKey: ["returns"] });
      queryClient.invalidateQueries({ queryKey: ["transactions"] });
      navigate(`/returns/${res.data.data.id}`);
    },
    onError: (err) => {
      const detail = err.response?.data?.detail;
      const msg = typeof detail === "string" ? detail : err.response?.data?.message || "Gagal memproses pengembalian";
      setServerError(msg);
    },
  });

  async function handleUpload() {
    if (!photoFile) return "";
    setUploading(true);
    try {
      const result = await uploadPhoto(photoFile);
      setPhotoUrl(result.url);
      return result.url;
    } catch (err) {
      setServerError("Gagal mengunggah foto: " + (err.response?.data?.detail || err.message));
      throw err;
    } finally {
      setUploading(false);
    }
  }

  async function handleSubmit(e) {
    e.preventDefault();
    if (!borrowId) return setServerError("Pilih transaksi terlebih dahulu");
    if (details.length === 0) return setServerError("Data komponen belum dimuat");
    if (isLate && !lateReason.trim()) return setServerError("Alasan keterlambatan wajib diisi karena pengembalian terlambat");

    // Validasi catatan kerusakan: wajib diisi jika kondisi Rusak
    const damagedWithoutNotes = details.flatMap((d) =>
      d.items.filter((it) => it.condition === "Rusak" && !it.notes.trim())
    );
    if (damagedWithoutNotes.length > 0) {
      return setServerError(
        `Catatan kerusakan wajib diisi untuk barang ${damagedWithoutNotes
          .map((it) => it.serial_number || `#${it.inventory_item_id}`)
          .join(", ")}`
      );
    }

    let finalPhotoUrl = photoUrl;
    if (photoFile && !photoUrl) {
      try {
        finalPhotoUrl = await handleUpload();
      } catch {
        return;
      }
    }

    mutation.mutate({ photo_url: finalPhotoUrl || undefined });
  }

  const totalItems = details.reduce((sum, d) => sum + d.items.length, 0);

  return (
    <div>
      <button onClick={() => navigate("/returns")} className="mb-4 flex items-center gap-1 text-sm text-gray-500 hover:text-slate-700"><ArrowLeft className="h-4 w-4" /> Kembali</button>
      <PageHeader title="Proses Pengembalian" description="Catat pengembalian inventaris yang sedang dipinjam per barang (SN)" />

      <form onSubmit={handleSubmit} className="space-y-6">
        {serverError && <div className="whitespace-pre-line rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{serverError}</div>}

        {/* Step 1: Pilih transaksi */}
        <div className="rounded-lg border border-gray-200 bg-white p-4">
          <h3 className="mb-3 text-sm font-semibold text-gray-700">1. Pilih Transaksi Peminjaman</h3>
          <select value={borrowId} onChange={(e) => handleSelectTx(e.target.value)}
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-slate-400 sm:w-96">
            <option value="">Pilih transaksi (status Dipinjam)...</option>
            {activeTxs.map((tx) => (
              <option key={tx.id} value={tx.id}>#{tx.id} · {tx.borrower?.borrower_name} ({formatDateLocal(tx.borrow_date)})</option>
            ))}
          </select>
        </div>

        {/* Petugas penerima */}
        <div className="rounded-lg border border-gray-200 bg-white p-4">
          <h3 className="mb-3 text-sm font-semibold text-gray-700">2. Petugas yang Menerima</h3>
          <select value={officerId} onChange={(e) => setOfficerId(e.target.value)}
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-slate-400 sm:w-72">
            <option value="">Pilih petugas (opsional)...</option>
            {officers.map((o) => (
              <option key={o.id} value={o.id}>{o.officer_name} {o.position ? `(${o.position})` : ""}</option>
            ))}
          </select>
          <p className="mt-1 text-xs text-gray-400">Petugas yang menerima barang kembali dari peminjam</p>
        </div>

        {/* Step 3: Kondisi per barang (SN) */}
        {details.length > 0 && (
          <div className="rounded-lg border border-gray-200 bg-white p-4">
            <h3 className="mb-3 text-sm font-semibold text-gray-700">3. Kondisi Pengembalian per Barang (SN)</h3>
            <div className="overflow-x-auto">
              {details.map((comp, compIdx) => (
                <div key={comp.inventory_component_id} className="mb-4 last:mb-0">
                  <p className="mb-2 text-sm font-medium text-slate-700">
                    {comp.item_name} · <span className="text-xs text-gray-400">{comp.items.length} SN</span>
                  </p>
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-gray-100 bg-gray-50 text-left">
                        <th className="px-3 py-2 font-semibold text-gray-600">Nomor Seri</th>
                        <th className="px-3 py-2 font-semibold text-gray-600">Kondisi</th>
                        <th className="px-3 py-2 font-semibold text-gray-600">Catatan <span className="text-red-400 text-[10px]">* jika rusak</span></th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                      {comp.items.map((it, itemIdx) => (
                        <tr key={it.inventory_item_id}>
                          <td className="px-3 py-2">
                            <span className="font-mono text-xs font-medium text-slate-800">{it.serial_number}</span>
                          </td>
                          <td className="px-3 py-2">
                            <select
                              value={it.condition}
                              onChange={(e) => updateItemCondition(compIdx, itemIdx, "condition", e.target.value)}
                              className={`rounded-md border px-2 py-1 text-sm outline-none focus:ring-1 ${
                                it.condition === "Baik" ? "border-emerald-300 bg-emerald-50 text-emerald-700" : "border-red-300 bg-red-50 text-red-700"
                              }`}
                            >
                              <option value="Baik">Baik</option>
                              <option value="Rusak">Rusak</option>
                            </select>
                          </td>
                          <td className="px-3 py-2">
                            <input
                              type="text"
                              placeholder={it.condition === "Rusak" ? "Wajib diisi, jelaskan kerusakan" : "Opsional"}
                              value={it.notes}
                              onChange={(e) => updateItemCondition(compIdx, itemIdx, "notes", e.target.value)}
                              className={`w-32 rounded-md border px-2 py-1 text-sm outline-none focus:ring-1 ${
                                it.condition === "Rusak" && !it.notes.trim()
                                  ? "border-red-300 bg-red-50 focus:ring-red-400"
                                  : "border-gray-300 focus:ring-slate-400"
                              }`}
                            />
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ))}
              <p className="mt-3 text-xs text-gray-500">Total: {totalItems} barang dikembalikan</p>
            </div>
          </div>
        )}

        {/* Step 4: Tanggal & Ganti rugi */}
        <div className="rounded-lg border border-gray-200 bg-white p-4">
          <h3 className="mb-3 text-sm font-semibold text-gray-700">4. Tanggal Pengembalian</h3>
          <div>
            <input type="date" value={returnDate} onChange={(e) => setReturnDate(e.target.value)}
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-slate-400 sm:w-56" />
            {selectedTx && (
              <p className="mt-1 text-xs text-gray-400">
                Rencana kembali: {formatDateLocal(selectedTx.expected_return_date)}
              </p>
            )}
          </div>

          {/* Late indicator */}
          {isLate && (
            <div className="mt-4 rounded-lg border border-red-200 bg-red-50 p-4">
              <p className="text-sm font-semibold text-red-700">
                ⚠ Pengembalian Terlambat {daysLate} hari dari rencana
              </p>
              <label className="mt-2 block text-xs font-medium text-gray-700">
                Alasan Keterlambatan <span className="text-red-500">*</span>
              </label>
              <textarea
                value={lateReason}
                onChange={(e) => setLateReason(e.target.value)}
                placeholder="Jelaskan alasan mengapa pengembalian terlambat..."
                rows={3}
                className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-slate-400"
              />
            </div>
          )}
        </div>

        {/* Step 5: Foto */}
        <div className="rounded-lg border border-gray-200 bg-white p-4">
          <h3 className="mb-3 text-sm font-semibold text-gray-700 flex items-center gap-1.5">
            <Camera className="h-4 w-4 text-gray-400" /> 5. Foto Dokumentasi (Opsional)
          </h3>
          <p className="mb-3 text-xs text-gray-500">Upload foto kondisi barang saat dikembalikan.</p>
          <div className="flex flex-wrap items-start gap-4">
            <div>
              <label className="inline-flex cursor-pointer items-center gap-1.5 rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-600 hover:bg-gray-50">
                <Camera className="h-4 w-4" />
                <span>{photoFile ? "Ganti Foto" : "Pilih Foto"}</span>
                <input type="file" accept="image/jpeg,image/png,image/webp"
                  onChange={(e) => {
                    const file = e.target.files?.[0];
                    if (!file) return;
                    setPhotoFile(file);
                    setPhotoPreview(URL.createObjectURL(file));
                    setPhotoUrl("");
                  }}
                  className="hidden" />
              </label>
            </div>
            {photoPreview && (
              <div className="relative inline-block">
                <img src={photoPreview} alt="Preview" className="h-24 w-24 rounded-md border border-gray-200 object-cover" />
                <button type="button" onClick={() => { setPhotoFile(null); setPhotoPreview(""); setPhotoUrl(""); }}
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

        {/* Step 6: Dokumen (info download setelah return) */}
        <div className="rounded-lg border border-gray-200 bg-white p-4">
          <h3 className="mb-3 text-sm font-semibold text-gray-700 flex items-center gap-1.5">
            <FileDown className="h-4 w-4 text-gray-400" /> 6. Dokumen Pengembalian
          </h3>
          <p className="text-xs text-gray-500">Setelah pengembalian dicatat, Anda dapat mengunduh template dokumen, menandatanganinya, dan mengunggah kembali dokumen yang sudah ditandatangani.</p>
        </div>

        <div className="flex justify-end gap-3">
          <button type="button" onClick={() => navigate("/returns")} className="rounded-md border border-gray-300 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50">Batal</button>
          <button type="submit" disabled={mutation.isPending || uploading}
            className="flex items-center gap-1 rounded-md bg-slate-800 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700 disabled:opacity-60">
            {mutation.isPending ? <><Loader2 className="h-4 w-4 animate-spin" /> Memproses...</> : "Proses Pengembalian"}
          </button>
        </div>
      </form>
    </div>
  );
}

function formatDateLocal(dateStr) {
  if (!dateStr) return "";
  const d = new Date(dateStr);
  return d.toLocaleDateString("id-ID", { day: "numeric", month: "short", year: "numeric" });
}
