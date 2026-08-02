import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { borrowApi } from "@/api/borrow";
import { borrowersApi } from "@/api/borrowers";
import { officersApi } from "@/api/officers";
import { inventoryApi } from "@/api/inventory";
import { uploadPhoto } from "@/api/upload";
import PageHeader from "@/components/ui/PageHeader";
import StatusBadge from "@/components/ui/StatusBadge";
import { ArrowLeft, Search, Plus, Trash2, Loader2, Camera, X } from "lucide-react";

/**
 * Halaman form peminjaman baru — multi-komponen dengan pilihan SN.
 * Langkah:
 * 1. Pilih peminjam
 * 2. Cari & tambah komponen ke "keranjang" — pilih SN individual
 * 3. Tentukan tanggal pinjam & kembali
 * 4. Submit
 */
export default function TransactionFormPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  // Step state
  const [borrowerId, setBorrowerId] = useState("");
  const [borrowDate, setBorrowDate] = useState(new Date().toISOString().split("T")[0]);
  const [returnDate, setReturnDate] = useState("");
  const [officerId, setOfficerId] = useState("");
  const [cart, setCart] = useState([]); // [{ component, selectedItems: [{id, serial_number}] }]
  const [compSearch, setCompSearch] = useState("");
  const [serverError, setServerError] = useState("");
  const [photoFile, setPhotoFile] = useState(null);
  const [photoPreview, setPhotoPreview] = useState("");
  const [photoUrl, setPhotoUrl] = useState("");
  const [uploading, setUploading] = useState(false);

  // SN selection modal state
  const [snModal, setSnModal] = useState(null); // { component } — show SN picker
  const [pendingCompItems, setPendingCompItems] = useState([]); // Available items for SN picker
  const [selectedSns, setSelectedSns] = useState(new Set()); // selected item IDs

  // Fetch borrowers
  const { data: borrowersRes } = useQuery({
    queryKey: ["borrowers", "all"],
    queryFn: () => borrowersApi.getBorrowers({ size: 100 }),
    staleTime: 2 * 60_000,
  });

  // Fetch officers for dropdown
  const { data: officersRes } = useQuery({
    queryKey: ["officers", "active"],
    queryFn: () => officersApi.getOfficers({ size: 100, is_active: true }),
    staleTime: 2 * 60_000,
  });

  // Fetch components for search
  const { data: compsRes } = useQuery({
    queryKey: ["components", "search", compSearch],
    queryFn: () => inventoryApi.getComponents({ size: 20, search: compSearch || undefined }),
    enabled: compSearch.length > 1,
  });

  const borrowers = borrowersRes?.data?.data || [];
  const officers = officersRes?.data?.data || [];
  const searchedComps = compsRes?.data?.data || [];

  /** Buka modal pilih SN untuk komponen tertentu */
  function openSnModal(comp) {
    // Ambil daftar item tersedia untuk komponen ini
    inventoryApi.getComponent(comp.id).then((res) => {
      const items = res?.data?.data?.items || [];
      const availableItems = items.filter((it) => it.status === "Available");
      setPendingCompItems(availableItems);
      setSnModal({ component: comp });
      setSelectedSns(new Set());
    }).catch(() => {
      // Fallback: tetap buka modal dengan data kosong
      setPendingCompItems([]);
      setSnModal({ component: comp });
      setSelectedSns(new Set());
    });
  }

  /** Toggle SN selection */
  function toggleSn(itemId) {
    const next = new Set(selectedSns);
    if (next.has(itemId)) next.delete(itemId);
    else next.add(itemId);
    setSelectedSns(next);
  }

  /** Konfirmasi pilihan SN — tambah ke cart */
  function confirmSnSelection() {
    if (!snModal) return;
    const chosen = pendingCompItems.filter((it) => selectedSns.has(it.id));
    if (chosen.length === 0) return;

    const exists = cart.find((c) => c.component.id === snModal.component.id);
    if (exists) {
      // Gabungkan dengan yang sudah ada
      const mergedItems = [...exists.selectedItems];
      for (const it of chosen) {
        if (!mergedItems.find((m) => m.id === it.id)) {
          mergedItems.push({ id: it.id, serial_number: it.serial_number });
        }
      }
      setCart(cart.map((c) =>
        c.component.id === snModal.component.id
          ? { ...c, selectedItems: mergedItems }
          : c
      ));
    } else {
      setCart([...cart, {
        component: snModal.component,
        selectedItems: chosen.map((it) => ({ id: it.id, serial_number: it.serial_number })),
      }]);
    }
    setSnModal(null);
    setCompSearch("");
  }

  /** Hapus satu SN dari cart */
  function removeSnFromCart(cartIdx, itemIdx) {
    const updated = cart.map((c, i) => {
      if (i !== cartIdx) return c;
      const newItems = c.selectedItems.filter((_, j) => j !== itemIdx);
      if (newItems.length === 0) return null; // akan dihapus
      return { ...c, selectedItems: newItems };
    }).filter(Boolean);
    setCart(updated);
  }

  /** Hapus seluruh komponen dari cart */
  function removeFromCart(idx) {
    setCart(cart.filter((_, i) => i !== idx));
  }

  /** Submit transaksi */
  const mutation = useMutation({
    mutationFn: ({ photo_url }) =>
        borrowApi.createTransaction({
          borrower_id: Number(borrowerId),
          issued_by: officerId ? Number(officerId) : undefined,
        borrow_date: borrowDate,
        expected_return_date: returnDate,
        photo: photo_url,
        details: cart.map((c) => ({
          inventory_component_id: c.component.id,
          quantity: c.selectedItems.length,
          inventory_item_ids: c.selectedItems.map((it) => it.id),
        })),
      }),
    onSuccess: (res) => {
      queryClient.invalidateQueries({ queryKey: ["transactions"] });
      navigate(`/borrow/transactions/${res.data.data.id}`);
    },
    onError: (err) => {
      const detail = err.response?.data?.detail;
      const msg = typeof detail === 'string' ? detail : (detail?.message || err.response?.data?.message || "Gagal membuat transaksi");
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
    setServerError("");

    if (!borrowerId) return setServerError("Pilih peminjam terlebih dahulu");
    if (!returnDate) return setServerError("Tanggal rencana kembali wajib diisi");
    if (returnDate < borrowDate) return setServerError("Tanggal kembali tidak boleh sebelum tanggal pinjam");
    if (cart.length === 0) return setServerError("Tambahkan minimal 1 unit dengan SN yang dipilih");

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

  const selectedBorrower = borrowers.find((b) => b.id === Number(borrowerId));

  return (
    <div>
      <button onClick={() => navigate("/borrow/transactions")} className="mb-4 flex items-center gap-1 text-sm text-gray-500 hover:text-slate-700">
        <ArrowLeft className="h-4 w-4" /> Kembali
      </button>

      <PageHeader title="Peminjaman Baru" description="Proses peminjaman inventaris: pilih peminjam, komponen dengan SN spesifik, dan tanggal" />

      <form onSubmit={handleSubmit} className="space-y-6">
        {serverError && (
          <div className="whitespace-pre-line rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{serverError}</div>
        )}

        {/* === STEP 1: Pilih Peminjam === */}
        <div className="rounded-lg border border-gray-200 bg-white p-4">
          <h3 className="mb-3 text-sm font-semibold text-gray-700">1. Pilih Peminjam</h3>
          <div className="flex flex-wrap items-center gap-3">
            <select value={borrowerId} onChange={(e) => setBorrowerId(e.target.value)}
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-slate-400 sm:w-72">
              <option value="">Pilih peminjam...</option>
              {borrowers.map((b) => (
                <option key={b.id} value={b.id}>{b.borrower_name} ({b.borrower_type})</option>
              ))}
            </select>
            {selectedBorrower && (
              <div className="flex items-center gap-2 text-sm text-gray-600">
                <span className="text-gray-400">{selectedBorrower.institution || "Tanpa instansi"}</span>
                <StatusBadge type="borrower" value={selectedBorrower.borrower_type} />
              </div>
            )}
          </div>
        </div>

        {/* === STEP 2: Petugas + Cart === */}
        <div className="rounded-lg border border-gray-200 bg-white p-4">
          <div className="mb-4">
            <label className="mb-1 block text-xs font-medium text-gray-600">Petugas yang Mengeluarkan</label>
            <select
              value={officerId}
              onChange={(e) => setOfficerId(e.target.value)}
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-slate-400 sm:w-72"
            >
              <option value="">Pilih petugas (opsional)...</option>
              {officers.map((o) => (
                <option key={o.id} value={o.id}>
                  {o.officer_name} {o.position ? `(${o.position})` : ""} {o.nip ? `- ${o.nip}` : ""}
                </option>
              ))}
            </select>
            <p className="mt-0.5 text-xs text-gray-400">Nama petugas yang menyerahkan barang ke peminjam</p>
          </div>

          <h3 className="mb-3 text-sm font-semibold text-gray-700">2. Tambah Unit (pilih per SN)</h3>

          {/* Search bar */}
          <div className="relative mb-4">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
            <input type="text" placeholder="Cari unit (nama, merek, SN)..." value={compSearch}
              onChange={(e) => setCompSearch(e.target.value)}
              className="w-full rounded-md border border-gray-300 py-2 pl-9 pr-3 text-sm outline-none focus:ring-2 focus:ring-slate-400" />
          </div>

          {/* Search results */}
          {compSearch.length > 1 && searchedComps.length > 0 && (
            <div className="mb-4 max-h-48 overflow-y-auto rounded-md border border-gray-200">
              {searchedComps.map((comp) => (
                <div key={comp.id} className="flex items-center justify-between border-b border-gray-100 px-3 py-2 text-sm last:border-0">
                  <div>
                    <p className="font-medium text-slate-700">{comp.item_name}</p>
                    <p className="text-xs text-gray-400">{comp.brand || "-"} | Tersedia: <span className="font-semibold text-emerald-600">{comp.available_quantity ?? 0}</span></p>
                  </div>
                  <button type="button" onClick={() => openSnModal(comp)}
                    className="flex items-center gap-1 rounded-md bg-slate-100 px-2 py-1 text-xs font-medium text-slate-700 hover:bg-slate-200">
                    <Plus className="h-3 w-3" /> Pilih SN
                  </button>
                </div>
              ))}
            </div>
          )}

          {/* Cart items */}
          {cart.length > 0 && (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-100 bg-gray-50 text-left">
                    <th className="px-3 py-2 font-semibold text-gray-600">Unit</th>
                    <th className="px-3 py-2 font-semibold text-gray-600">SN Dipilih</th>
                    <th className="px-3 py-2 font-semibold text-gray-600">Jumlah</th>
                    <th className="px-3 py-2 font-semibold text-gray-600"></th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {cart.map((c, idx) => (
                    <tr key={c.component.id}>
                      <td className="px-3 py-2">
                        <p className="font-medium text-slate-800">{c.component.item_name}</p>
                        <p className="text-xs text-gray-400">{c.component.brand || "-"}</p>
                      </td>
                      <td className="px-3 py-2">
                        <div className="flex flex-wrap gap-1">
                          {c.selectedItems.map((it, snIdx) => (
                            <span key={it.id} className="inline-flex items-center gap-0.5 rounded bg-blue-50 px-1.5 py-0.5 text-xs font-mono text-blue-700">
                              {it.serial_number || `#${it.id}`}
                              <button type="button" onClick={() => removeSnFromCart(idx, snIdx)}
                                className="ml-0.5 text-blue-400 hover:text-red-500">&times;</button>
                            </span>
                          ))}
                          <button type="button" onClick={() => openSnModal(c.component)}
                            className="inline-flex items-center gap-0.5 rounded px-1 py-0.5 text-xs text-blue-500 hover:bg-blue-50">
                            <Plus className="h-3 w-3" /> Tambah SN
                          </button>
                        </div>
                      </td>
                      <td className="px-3 py-2">
                        <span className="font-medium">{c.selectedItems.length}</span>
                      </td>
                      <td className="px-3 py-2">
                        <button type="button" onClick={() => removeFromCart(idx)}
                          className="rounded-md p-1 text-red-500 hover:bg-red-50">
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <p className="mt-2 text-xs text-gray-500">
                Total: {cart.length} jenis unit, {cart.reduce((sum, c) => sum + c.selectedItems.length, 0)} item
              </p>
            </div>
          )}

          {cart.length === 0 && !compSearch && (
            <p className="py-4 text-center text-sm text-gray-400">Ketik nama unit di atas untuk mencari dan menambahkannya ke daftar pinjaman.</p>
          )}
        </div>

        {/* === STEP 3: Tanggal === */}
        <div className="rounded-lg border border-gray-200 bg-white p-4">
          <h3 className="mb-3 text-sm font-semibold text-gray-700">3. Tanggal Peminjaman</h3>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <label className="mb-1 block text-xs font-medium text-gray-600">Tanggal Pinjam</label>
              <input type="date" value={borrowDate} onChange={(e) => setBorrowDate(e.target.value)}
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-slate-400" />
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium text-gray-600">Rencana Kembali <span className="text-red-500">*</span></label>
              <input type="date" value={returnDate} onChange={(e) => setReturnDate(e.target.value)}
                min={borrowDate}
                className={`w-full rounded-md border px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-slate-400 ${!returnDate && serverError ? "border-red-400" : "border-gray-300"}`} />
            </div>
          </div>
        </div>

        {/* === STEP 4: Foto Dokumentasi === */}
        <div className="rounded-lg border border-gray-200 bg-white p-4">
          <h3 className="mb-3 text-sm font-semibold text-gray-700 flex items-center gap-1.5">
            <Camera className="h-4 w-4 text-gray-400" /> 4. Foto Dokumentasi (Opsional)
          </h3>
          <p className="mb-3 text-xs text-gray-500">Upload foto saat barang diserahkan kepada peminjam.</p>
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

        {/* Submit */}
        <div className="flex justify-end gap-3">
          <button type="button" onClick={() => navigate("/borrow/transactions")}
            className="rounded-md border border-gray-300 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50">Batal</button>
          <button type="submit" disabled={mutation.isPending}
            className="flex items-center gap-1 rounded-md bg-slate-800 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-60">
            {mutation.isPending ? <><Loader2 className="h-4 w-4 animate-spin" /> Memproses...</> : "Proses Peminjaman"}
          </button>
        </div>
      </form>

      {/* Modal pilih SN */}
      {snModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="w-full max-w-md rounded-lg bg-white p-6 shadow-xl">
            <h3 className="mb-2 text-base font-semibold text-slate-800">
              Pilih Serial Number: {snModal.component.item_name}
            </h3>
            <p className="mb-4 text-xs text-gray-500">
              {snModal.component.brand || "-"} | Tersedia: {snModal.component.available_quantity ?? 0} | Pilih SN yang akan dipinjam.
            </p>

            {pendingCompItems.length === 0 ? (
              <p className="py-6 text-center text-sm text-gray-400">Tidak ada item tersedia untuk unit ini.</p>
            ) : (
              <div className="mb-4 max-h-56 overflow-y-auto rounded-md border border-gray-200">
                {pendingCompItems.map((it) => (
                  <label key={it.id}
                    className={`flex cursor-pointer items-center gap-3 border-b border-gray-100 px-3 py-2 text-sm last:border-0 hover:bg-slate-50 ${
                      selectedSns.has(it.id) ? "bg-blue-50" : ""
                    }`}>
                    <input type="checkbox" checked={selectedSns.has(it.id)}
                      onChange={() => toggleSn(it.id)}
                      className="h-4 w-4 rounded border-gray-300 text-slate-800 focus:ring-slate-400" />
                    <span className="font-mono text-xs text-slate-700">{it.serial_number || `Item #${it.id}`}</span>
                    <span className="ml-auto text-xs text-emerald-600">Available</span>
                  </label>
                ))}
              </div>
            )}

            <div className="flex justify-between items-center">
              <p className="text-xs text-gray-500">
                {selectedSns.size} item dipilih
              </p>
              <div className="flex gap-2">
                <button type="button" onClick={() => setSnModal(null)}
                  className="rounded-md border border-gray-300 px-3 py-1.5 text-sm text-gray-600 hover:bg-gray-50">Batal</button>
                <button type="button" onClick={confirmSnSelection}
                  disabled={selectedSns.size === 0}
                  className="rounded-md bg-slate-800 px-3 py-1.5 text-sm font-medium text-white hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-50">
                  Tambah ke Daftar
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
