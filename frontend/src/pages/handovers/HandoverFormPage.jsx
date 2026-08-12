import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { handoversApi } from "@/api/handovers";
import { inventoryApi } from "@/api/inventory";
import { officersApi } from "@/api/officers";
import { uploadPhoto } from "@/api/upload";
import PageHeader from "@/components/ui/PageHeader";
import { ArrowLeft, Search, Plus, Trash2, Loader2, Camera, X } from "lucide-react";

export default function HandoverFormPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [uptReceiver, setUptReceiver] = useState("");
  const [handoverDate, setHandoverDate] = useState(new Date().toISOString().split("T")[0]);
  const [officerId, setOfficerId] = useState("");
  const [notes, setNotes] = useState("");
  const [cart, setCart] = useState([]); // selected items
  const [compSearch, setCompSearch] = useState("");
  const [serverError, setServerError] = useState("");
  const [photoFile, setPhotoFile] = useState(null);
  const [photoPreview, setPhotoPreview] = useState("");
  const [photoUrl, setPhotoUrl] = useState("");
  const [uploading, setUploading] = useState(false);

  // SN selection modal
  const [snModal, setSnModal] = useState(null);
  const [pendingItems, setPendingItems] = useState([]);
  const [selectedSns, setSelectedSns] = useState(new Set());

  // Officers
  const { data: officersRes } = useQuery({
    queryKey: ["officers", "active"],
    queryFn: () => officersApi.getOfficers({ size: 100, is_active: true }),
    staleTime: 2 * 60_000,
  });
  const officers = officersRes?.data?.data || [];

  // Search components
  const { data: compsRes } = useQuery({
    queryKey: ["components", "search", compSearch],
    queryFn: () => inventoryApi.getComponents({ size: 20, search: compSearch || undefined }),
    enabled: compSearch.length > 1,
  });
  const searchedComps = compsRes?.data?.data || [];

  function openSnModal(comp) {
    inventoryApi.getComponent(comp.id).then((res) => {
      const items = res?.data?.data?.items || [];
      const availableItems = items.filter((it) => it.status === "Available");
      // Filter out already selected items
      const alreadySelected = new Set(cart.map((c) => c.id));
      setPendingItems(availableItems.filter((it) => !alreadySelected.has(it.id)));
      setSnModal({ component: comp });
      setSelectedSns(new Set());
    });
  }

  function toggleSn(itemId) {
    const next = new Set(selectedSns);
    if (next.has(itemId)) next.delete(itemId);
    else next.add(itemId);
    setSelectedSns(next);
  }

  function confirmSnSelection() {
    if (!snModal) return;
    const chosen = pendingItems.filter((it) => selectedSns.has(it.id));
    if (chosen.length === 0) return;
    setCart([...cart, ...chosen.map((it) => ({ id: it.id, serial_number: it.serial_number, component_name: snModal.component.item_name }))]);
    setSnModal(null);
    setCompSearch("");
  }

  function removeFromCart(idx) {
    setCart(cart.filter((_, i) => i !== idx));
  }

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

  const mutation = useMutation({
    mutationFn: ({ photo_url }) =>
      handoversApi.createHandover({
        upt_receiver: uptReceiver,
        issued_by: officerId ? Number(officerId) : undefined,
        handover_date: handoverDate,
        photo: photo_url,
        notes: notes || undefined,
        items: cart.map((it) => ({ inventory_item_id: it.id })),
      }),
    onSuccess: (res) => {
      queryClient.invalidateQueries({ queryKey: ["handovers"] });
      navigate(`/handovers/${res.data.data.id}`);
    },
    onError: (err) => {
      const detail = err.response?.data?.detail;
      const msg = typeof detail === 'string' ? detail : (detail?.message || "Gagal membuat pelimpahan");
      setServerError(msg);
    },
  });

  async function handleSubmit(e) {
    e.preventDefault();
    setServerError("");
    if (!uptReceiver.trim()) return setServerError("UPT Penerima wajib diisi");
    if (!handoverDate) return setServerError("Tanggal pelimpahan wajib diisi");
    if (cart.length === 0) return setServerError("Pilih minimal 1 barang dengan SN");

    let finalPhotoUrl = photoUrl;
    if (photoFile && !photoUrl) {
      try { finalPhotoUrl = await handleUpload(); } catch { return; }
    }
    mutation.mutate({ photo_url: finalPhotoUrl || undefined });
  }

  return (
    <div>
      <button onClick={() => navigate("/handovers")} className="mb-4 flex items-center gap-1 text-sm text-gray-500 hover:text-slate-700">
        <ArrowLeft className="h-4 w-4" /> Kembali
      </button>
      <PageHeader title="Pelimpahan Baru" description="Proses pelimpahan barang ke UPT: barang tidak akan dikembalikan" />

      <form onSubmit={handleSubmit} className="space-y-6">
        {serverError && (
          <div className="whitespace-pre-line rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{serverError}</div>
        )}

        {/* UPT Penerima + Tanggal */}
        <div className="rounded-lg border border-gray-200 bg-white p-4">
          <h3 className="mb-3 text-sm font-semibold text-gray-700">Info Pelimpahan</h3>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <label className="mb-1 block text-xs font-medium text-gray-600">UPT Penerima <span className="text-red-500">*</span></label>
              <input type="text" value={uptReceiver} onChange={(e) => setUptReceiver(e.target.value)}
                placeholder="contoh: UPT BMKG Bandung"
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-slate-400" />
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium text-gray-600">Tanggal Pelimpahan <span className="text-red-500">*</span></label>
              <input type="date" value={handoverDate} onChange={(e) => setHandoverDate(e.target.value)}
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-slate-400" />
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium text-gray-600">Petugas</label>
              <select value={officerId} onChange={(e) => setOfficerId(e.target.value)}
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-slate-400">
                <option value="">Pilih petugas (opsional)...</option>
                {officers.map((o) => (
                  <option key={o.id} value={o.id}>{o.officer_name} {o.position ? `(${o.position})` : ""}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium text-gray-600">Catatan</label>
              <textarea value={notes} onChange={(e) => setNotes(e.target.value)} rows={2}
                placeholder="Catatan opsional..."
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-slate-400" />
            </div>
          </div>
        </div>

        {/* Pilih Barang */}
        <div className="rounded-lg border border-gray-200 bg-white p-4">
          <h3 className="mb-3 text-sm font-semibold text-gray-700">Pilih Barang yang Dilimpahkan</h3>

          <div className="relative mb-4">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
            <input type="text" placeholder="Cari unit..." value={compSearch}
              onChange={(e) => setCompSearch(e.target.value)}
              className="w-full rounded-md border border-gray-300 py-2 pl-9 pr-3 text-sm outline-none focus:ring-2 focus:ring-slate-400" />
          </div>

          {compSearch.length > 1 && searchedComps.length > 0 && (
            <div className="mb-4 max-h-48 overflow-y-auto rounded-md border border-gray-200">
              {searchedComps.map((comp) => (
                <div key={comp.id} className="flex items-center justify-between border-b border-gray-100 px-3 py-2 text-sm last:border-0">
                  <div>
                    <p className="font-medium text-slate-700">{comp.item_name}</p>
                    <p className="text-xs text-gray-400">Tersedia: <span className="font-semibold text-emerald-600">{comp.available_quantity ?? 0}</span></p>
                  </div>
                  <button type="button" onClick={() => openSnModal(comp)}
                    className="flex items-center gap-1 rounded-md bg-slate-100 px-2 py-1 text-xs font-medium text-slate-700 hover:bg-slate-200">
                    <Plus className="h-3 w-3" /> Pilih SN
                  </button>
                </div>
              ))}
            </div>
          )}

          {cart.length > 0 && (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-100 bg-gray-50 text-left">
                    <th className="px-3 py-2 font-semibold text-gray-600">Unit</th>
                    <th className="px-3 py-2 font-semibold text-gray-600">Nomor Seri</th>
                    <th className="px-3 py-2 font-semibold text-gray-600"></th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {cart.map((item, idx) => (
                    <tr key={`${item.id}-${idx}`}>
                      <td className="px-3 py-2 text-sm text-slate-700">{item.component_name}</td>
                      <td className="px-3 py-2">
                        <span className="font-mono text-xs text-slate-700">{item.serial_number || `#${item.id}`}</span>
                      </td>
                      <td className="px-3 py-2">
                        <button type="button" onClick={() => removeFromCart(idx)}
                          className="rounded-md p-1 text-red-500 hover:bg-red-50"><Trash2 className="h-4 w-4" /></button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <p className="mt-2 text-xs text-gray-500">Total: {cart.length} barang</p>
            </div>
          )}

          {cart.length === 0 && !compSearch && (
            <p className="py-4 text-center text-sm text-gray-400">Ketik nama unit di atas untuk mencari dan menambahkan barang.</p>
          )}
        </div>

        {/* Foto */}
        <div className="rounded-lg border border-gray-200 bg-white p-4">
          <h3 className="mb-3 text-sm font-semibold text-gray-700 flex items-center gap-1.5">
            <Camera className="h-4 w-4 text-gray-400" /> Foto Dokumentasi (Opsional)
          </h3>
          <div className="flex flex-wrap items-start gap-4">
            <label className="inline-flex cursor-pointer items-center gap-1.5 rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-600 hover:bg-gray-50">
              <Camera className="h-4 w-4" />
              <span>{photoFile ? "Ganti Foto" : "Pilih Foto"}</span>
              <input type="file" accept="image/jpeg,image/png,image/webp"
                onChange={(e) => {
                  const f = e.target.files?.[0];
                  if (!f) return;
                  setPhotoFile(f);
                  setPhotoPreview(URL.createObjectURL(f));
                  setPhotoUrl("");
                }}
                className="hidden" />
            </label>
            {photoPreview && (
              <div className="relative inline-block">
                <img src={photoPreview} alt="Preview" className="h-24 w-24 rounded-md object-cover" />
                <button type="button" onClick={() => { setPhotoFile(null); setPhotoPreview(""); setPhotoUrl(""); }}
                  className="absolute -right-1.5 -top-1.5 rounded-full bg-red-500 p-0.5 text-white hover:bg-red-600"><X className="h-3 w-3" /></button>
              </div>
            )}
            {uploading && <span className="flex items-center gap-1 text-sm text-blue-600"><Loader2 className="h-3 w-3 animate-spin" /> Mengunggah...</span>}
          </div>
        </div>

        <div className="flex justify-end gap-3">
          <button type="button" onClick={() => navigate("/handovers")}
            className="rounded-md border border-gray-300 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50">Batal</button>
          <button type="submit" disabled={mutation.isPending}
            className="flex items-center gap-1 rounded-md bg-slate-800 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700 disabled:opacity-60">
            {mutation.isPending ? <><Loader2 className="h-4 w-4 animate-spin" /> Memproses...</> : "Proses Pelimpahan"}
          </button>
        </div>
      </form>

      {/* Modal pilih SN */}
      {snModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="w-full max-w-md rounded-lg bg-white p-6 shadow-xl">
            <h3 className="mb-2 text-base font-semibold text-slate-800">
              Pilih Nomor Seri: {snModal.component.item_name}
            </h3>
            {pendingItems.length === 0 ? (
              <p className="py-6 text-center text-sm text-gray-400">Tidak ada item Tersedia untuk unit ini.</p>
            ) : (
              <div className="mb-4 max-h-56 overflow-y-auto rounded-md border border-gray-200">
                {pendingItems.map((it) => (
                  <label key={it.id}
                    className={`flex cursor-pointer items-center gap-3 border-b border-gray-100 px-3 py-2 text-sm last:border-0 hover:bg-slate-50 ${selectedSns.has(it.id) ? "bg-blue-50" : ""}`}>
                    <input type="checkbox" checked={selectedSns.has(it.id)}
                      onChange={() => toggleSn(it.id)}
                      className="h-4 w-4 rounded border-gray-300" />
                    <span className="font-mono text-xs">{it.serial_number || `#${it.id}`}</span>
                  </label>
                ))}
              </div>
            )}
            <div className="flex justify-between items-center">
              <p className="text-xs text-gray-500">{selectedSns.size} dipilih</p>
              <div className="flex gap-2">
                <button type="button" onClick={() => setSnModal(null)}
                  className="rounded-md border border-gray-300 px-3 py-1.5 text-sm text-gray-600 hover:bg-gray-50">Batal</button>
                <button type="button" onClick={confirmSnSelection} disabled={selectedSns.size === 0}
                  className="rounded-md bg-slate-800 px-3 py-1.5 text-sm font-medium text-white hover:bg-slate-700 disabled:opacity-50">Tambah</button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
