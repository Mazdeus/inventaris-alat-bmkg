import { useState, useRef } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient, keepPreviousData } from "@tanstack/react-query";
import { borrowApi } from "@/api/borrow";
import { useAuth } from "@/contexts/AuthContext";
import PageHeader from "@/components/ui/PageHeader";
import StatusBadge from "@/components/ui/StatusBadge";
import { ConfirmDialog } from "@/components/ui/ConfirmDialog";
import { formatDate } from "@/lib/formatters";
import { ArrowLeft, User, Calendar, FileDown, FileUp, Check, X, Ban, Loader2, Clock } from "lucide-react";

/**
 * Detail transaksi peminjaman + rincian komponen + dokumen tanda tangan.
 */
export default function TransactionDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { isAdmin } = useAuth();
  const fileInputRef = useRef(null);

  // Confirm dialogs
  const [approveOpen, setApproveOpen] = useState(false);
  const [rejectOpen, setRejectOpen] = useState(false);
  const [cancelOpen, setCancelOpen] = useState(false);

  // Extension state
  const [extModalOpen, setExtModalOpen] = useState(false);
  const [extendDate, setExtendDate] = useState("");
  const [extendReason, setExtendReason] = useState("");
  const [extError, setExtError] = useState("");

  const { data, isLoading, isError } = useQuery({
    queryKey: ["transaction", id],
    queryFn: () => borrowApi.getTransaction(Number(id)),
    enabled: !!id,
    placeholderData: keepPreviousData,
  });

  const tx = data?.data?.data;

  // Download document
  function handleDownloadDoc() {
    borrowApi.downloadDocument(tx.id).then((res) => {
      const blob = new Blob([res.data], { type: "text/plain" });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `peminjaman_${tx.id}.txt`;
      a.click();
      window.URL.revokeObjectURL(url);
    }).catch(() => {});
  }

  // Extension mutations
  const extMut = useMutation({
    mutationFn: () => borrowApi.requestExtension(tx.id, { requested_return_date: extendDate, reason: extendReason }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["transaction", id] });
      setExtModalOpen(false);
      setExtendDate("");
      setExtendReason("");
      setExtError("");
    },
    onError: (err) => setExtError(err.response?.data?.detail || "Gagal mengajukan perpanjangan"),
  });

  const extApproveMut = useMutation({
    mutationFn: (extId) => borrowApi.approveExtension(tx?.id, extId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["transaction", id] }),
  });

  const extRejectMut = useMutation({
    mutationFn: (extId) => borrowApi.rejectExtension(tx?.id, extId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["transaction", id] }),
  });

  const uploadMut = useMutation({
    mutationFn: (file) => borrowApi.uploadDocument(tx.id, file),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["transaction", id] }),
  });

  function handleUploadFile(e) {
    const file = e.target.files?.[0];
    if (!file) return;
    uploadMut.mutate(file);
    e.target.value = "";
  }

  // Admin actions
  const adminMut = useMutation({
    mutationFn: ({ action, txId }) => {
      if (action === "approve") return borrowApi.approve(txId);
      if (action === "reject") return borrowApi.reject(txId, "Ditolak oleh admin");
      if (action === "cancel") return borrowApi.cancel(txId);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["transaction", id] });
      setApproveOpen(false);
      setRejectOpen(false);
      setCancelOpen(false);
    },
  });

  if (isLoading) {
    return <div className="space-y-4"><div className="h-6 w-40 animate-pulse rounded bg-gray-200" /><div className="h-60 animate-pulse rounded-lg bg-gray-200" /></div>;
  }

  if (isError || !tx) {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 p-6 text-center text-red-700">
        Gagal memuat data transaksi.
        <button onClick={() => navigate("/borrow/transactions")} className="mt-2 text-sm underline">Kembali ke daftar</button>
      </div>
    );
  }

  return (
    <div>
      <button onClick={() => navigate("/borrow/transactions")} className="mb-4 flex items-center gap-1 text-sm text-gray-500 hover:text-slate-700">
        <ArrowLeft className="h-4 w-4" /> Kembali ke daftar
      </button>

      <PageHeader title={`Transaksi #${tx.id}`} description="Detail transaksi peminjaman" />

      {/* Info cards */}
      <div className="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <InfoCard icon={User} label="Peminjam" value={tx.borrower?.borrower_name} sub={tx.borrower?.institution} />
        <InfoCard icon={User} label="Diproses Oleh" value={tx.officer?.officer_name || "-"} />
        <InfoCard icon={Calendar} label="Tanggal Pinjam" value={formatDate(tx.borrow_date)} />
        <InfoCard icon={Calendar} label="Rencana Kembali" value={formatDate(tx.expected_return_date)} />
      </div>

      {/* Status badge */}
      <div className="mb-6">
        <p className="mb-1 text-xs text-gray-500">Status Transaksi</p>
        <StatusBadge type="borrow" value={tx.status} />
      </div>

      {/* Foto Dokumentasi */}
      {tx.photo && (
        <div className="mb-6 rounded-lg border border-gray-200 bg-white p-4">
          <p className="mb-2 text-xs font-medium uppercase text-gray-500">Foto Dokumentasi Peminjaman</p>
          <img
            src={`/uploads/${tx.photo}`}
            alt="Foto peminjaman"
            className="max-h-64 rounded-md object-cover"
            onError={(e) => { e.target.style.display = "none"; }}
          />
        </div>
      )}

      {/* Admin: Aksi berdasarkan status */}
      {isAdmin && (
        <div className="mb-6 rounded-lg border border-gray-200 bg-white p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-semibold text-gray-700">Aksi Admin</p>
              <p className="mt-1 text-xs text-gray-500">
                Status saat ini: <strong>{tx.status}</strong>
              </p>
            </div>
            <div className="flex items-center gap-2">
              {tx.status === "Menunggu" && (
                <>
                  <button
                    onClick={() => setApproveOpen(true)}
                    className="flex items-center gap-1 rounded-md bg-emerald-600 px-3 py-2 text-xs font-medium text-white hover:bg-emerald-700"
                  >
                    <Check className="h-3.5 w-3.5" /> Setujui
                  </button>
                  <button
                    onClick={() => setRejectOpen(true)}
                    className="flex items-center gap-1 rounded-md bg-red-600 px-3 py-2 text-xs font-medium text-white hover:bg-red-700"
                  >
                    <X className="h-3.5 w-3.5" /> Tolak
                  </button>
                </>
              )}
              {tx.status === "Dipinjam" && (
                <button
                  onClick={() => setCancelOpen(true)}
                  className="flex items-center gap-1 rounded-md bg-orange-600 px-3 py-2 text-xs font-medium text-white hover:bg-orange-700"
                >
                  <Ban className="h-3.5 w-3.5" /> Batalkan
                </button>
              )}
              {tx.status !== "Menunggu" && tx.status !== "Dipinjam" && (
                <p className="text-xs text-gray-400">Tidak ada aksi yang tersedia</p>
              )}
            </div>
          </div>
          {adminMut.isPending && (
            <p className="mt-2 flex items-center gap-1 text-xs text-blue-600"><Loader2 className="h-3 w-3 animate-spin" /> Memproses...</p>
          )}
          {adminMut.isError && (
            <p className="mt-2 text-xs text-red-600">{adminMut.error?.response?.data?.detail || "Gagal memproses"}</p>
          )}
        </div>
      )}

      {/* Section Perpanjangan */}
      {tx && (
      <div className="mb-6 rounded-lg border border-gray-200 bg-white p-4">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-semibold text-gray-700 flex items-center gap-1.5">
              <Clock className="h-4 w-4 text-gray-400" /> Perpanjangan Peminjaman
            </p>
          </div>
          <div className="flex items-center gap-2">
            {tx.extension?.status === "Menunggu" && (
              <span className="rounded-full bg-amber-100 px-2.5 py-0.5 text-xs font-medium text-amber-700">
                Menunggu Persetujuan
              </span>
            )}
            {tx.extension?.status === "Disetujui" && (
              <span className="rounded-full bg-emerald-100 px-2.5 py-0.5 text-xs font-medium text-emerald-700">
                Disetujui
              </span>
            )}
            {tx.extension?.status === "Ditolak" && (
              <span className="rounded-full bg-red-100 px-2.5 py-0.5 text-xs font-medium text-red-700">
                Ditolak
              </span>
            )}
            {!tx.extension && tx.status === "Dipinjam" && (
              <button onClick={() => setExtModalOpen(true)}
                className="flex items-center gap-1 rounded-md bg-amber-600 px-3 py-2 text-xs font-medium text-white hover:bg-amber-700">
                <Clock className="h-3.5 w-3.5" /> Ajukan Perpanjangan
              </button>
            )}
          </div>
        </div>
        {tx?.extension?.status === "Menunggu" && (
          <div className="mt-2 border-t border-gray-100 pt-2">
            <div className="flex items-center justify-between">
              <div className="text-xs text-gray-500">
                Diajukan: {tx.extension.new_date || "-"} · Alasan: {tx.extension.reason || "-"}
              </div>
              {isAdmin && (
                <div className="flex items-center gap-2">
                  <button onClick={() => tx.extension && extApproveMut.mutate(tx.extension.id)}
                    disabled={extApproveMut.isPending}
                    className="flex items-center gap-1 rounded-md bg-emerald-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-emerald-700 disabled:opacity-50">
                    {extApproveMut.isPending ? <><Loader2 className="h-3 w-3 animate-spin" />...</> : <><Check className="h-3 w-3" />Setujui</>}
                  </button>
                  <button onClick={() => tx.extension && extRejectMut.mutate(tx.extension.id)}
                    disabled={extRejectMut.isPending}
                    className="flex items-center gap-1 rounded-md bg-red-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-red-700 disabled:opacity-50">
                    {extRejectMut.isPending ? <><Loader2 className="h-3 w-3 animate-spin" />...</> : <><X className="h-3 w-3" />Tolak</>}
                  </button>
                </div>
              )}
            </div>
          </div>
        )}
        {tx?.extension?.status === "Disetujui" && (
          <div className="mt-2 border-t border-gray-100 pt-2 text-xs text-gray-500">
            Kembali: {tx.extension.new_date || "-"} · Alasan: {tx.extension.reason || "-"}
          </div>
        )}
        {tx?.extension?.status === "Ditolak" && (
          <div className="mt-2 border-t border-gray-100 pt-2 text-xs text-gray-500">
            Alasan: {tx.extension.reason || "-"}
          </div>
        )}
      </div>
      )}

      {/* Section Dokumen */}
      <div className="mb-6 rounded-lg border border-gray-200 bg-white p-4">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-semibold text-gray-700 flex items-center gap-1.5">
              <FileDown className="h-4 w-4 text-gray-400" /> Dokumen Peminjaman
            </p>
            <p className="mt-1 text-xs text-gray-500">
              {tx.signed_document
                ? "Dokumen sudah ditandatangani dan diupload."
                : "Unduh, tanda tangani, lalu unggah kembali dokumen yang sudah ditandatangani."}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <button onClick={handleDownloadDoc}
              className="flex items-center gap-1 rounded-md border border-gray-300 bg-white px-3 py-2 text-xs text-gray-700 hover:bg-gray-50">
              <FileDown className="h-3.5 w-3.5" /> Unduh Dokumen
            </button>
            <label className="flex cursor-pointer items-center gap-1 rounded-md bg-slate-800 px-3 py-2 text-xs font-medium text-white hover:bg-slate-700">
              <FileUp className="h-3.5 w-3.5" /> Unggah Tertandatangan
              <input type="file" ref={fileInputRef} accept=".pdf,.png,.jpg,.jpeg"
                onChange={handleUploadFile} className="hidden" />
            </label>
          </div>
        </div>
        {uploadMut.isPending && (
          <p className="mt-2 flex items-center gap-1 text-xs text-blue-600"><Loader2 className="h-3 w-3 animate-spin" /> Mengunggah...</p>
        )}
        {uploadMut.isError && (
          <p className="mt-2 text-xs text-red-600">Gagal mengunggah: {uploadMut.error?.response?.data?.detail || "Error"}</p>
        )}
        {tx.signed_document && (
          <div className="mt-3">
            <p className="text-xs text-emerald-600 font-medium">✓ Dokumen tertandatangan sudah diunggah</p>
            <a href={`/uploads/${tx.signed_document}`} target="_blank" rel="noopener noreferrer"
              className="mt-1 inline-block text-xs text-blue-600 underline hover:text-blue-800">
              Lihat Dokumen
            </a>
          </div>
        )}
      </div>

      {/* Extension Modal */}
      {extModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="w-full max-w-md rounded-lg bg-white p-6 shadow-xl">
            <h3 className="mb-2 text-base font-semibold text-slate-800">Ajukan Perpanjangan</h3>
            <p className="mb-4 text-xs text-gray-500">
              Transaksi #{tx.id} · Rencana kembali saat ini: {formatDate(tx.expected_return_date)}
            </p>
            {extError && <div className="mb-3 rounded bg-red-50 px-3 py-2 text-xs text-red-700">{extError}</div>}
            <div className="mb-3">
              <label className="mb-1 block text-xs font-medium text-gray-700">Tanggal Kembali Baru <span className="text-red-500">*</span></label>
              <input type="date" value={extendDate} min={tx.expected_return_date}
                onChange={(e) => setExtendDate(e.target.value)}
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-slate-400" />
            </div>
            <div className="mb-4">
              <label className="mb-1 block text-xs font-medium text-gray-700">Alasan Perpanjangan <span className="text-red-500">*</span></label>
              <textarea value={extendReason} onChange={(e) => setExtendReason(e.target.value)}
                placeholder="Jelaskan alasan perpanjangan..."
                rows={3}
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-slate-400" />
            </div>
            <div className="flex justify-end gap-2">
              <button onClick={() => { setExtModalOpen(false); setExtError(""); }}
                className="rounded-md border border-gray-300 px-3 py-1.5 text-sm text-gray-600 hover:bg-gray-50">Batal</button>
              <button onClick={() => extMut.mutate()} disabled={extMut.isPending || !extendDate || !extendReason.trim()}
                className="flex items-center gap-1 rounded-md bg-slate-800 px-3 py-1.5 text-sm font-medium text-white hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-50">
                {extMut.isPending ? <><Loader2 className="h-3.5 w-3.5 animate-spin" /> Mengirim...</> : "Ajukan"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Confirm Approve */}
      <ConfirmDialog open={approveOpen} onOpenChange={setApproveOpen}
        title="Setujui Peminjaman" message="Setujui transaksi peminjaman ini? Stok akan dipindahkan ke status Dipinjam."
        onConfirm={() => adminMut.mutate({ action: "approve", txId: tx.id })}
        confirmLabel="Setujui" variant="default" />

      {/* Confirm Reject */}
      <ConfirmDialog open={rejectOpen} onOpenChange={setRejectOpen}
        title="Tolak Peminjaman" message="Tolak transaksi peminjaman ini?"
        onConfirm={() => adminMut.mutate({ action: "reject", txId: tx.id })}
        confirmLabel="Tolak" variant="danger" />

      {/* Confirm Cancel */}
      <ConfirmDialog open={cancelOpen} onOpenChange={setCancelOpen}
        title="Batalkan Transaksi" message="Batalkan transaksi ini? Stok akan dikembalikan ke inventaris."
        onConfirm={() => adminMut.mutate({ action: "cancel", txId: tx.id })}
        confirmLabel="Batalkan" variant="danger" />

      {/* Detail komponen */}
      <div className="rounded-lg border border-gray-200 bg-white">
        <div className="border-b border-gray-100 px-4 py-3">
          <h3 className="text-sm font-semibold text-gray-700">Unit yang Dipinjam</h3>
        </div>
        {!tx.details?.length ? (
          <div className="p-8 text-center text-sm text-gray-400">Tidak ada detail komponen</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-100 bg-gray-50 text-left">
                  <th className="px-4 py-3 font-semibold text-gray-600">Nama Unit</th>
                  <th className="px-4 py-3 font-semibold text-gray-600">Merek</th>
                  <th className="px-4 py-3 font-semibold text-gray-600">Nomor Seri Dipilih</th>
                  <th className="px-4 py-3 font-semibold text-gray-600">Jumlah</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {tx.details.map((d) => {
                  const selectedSns = d.selected_items || [];
                  return (
                  <tr key={d.id}>
                    <td className="px-4 py-3 font-medium text-slate-800">{d.component?.item_name || "-"}</td>
                    <td className="px-4 py-3 text-gray-600">{d.component?.brand || "-"}</td>
                    <td className="px-4 py-3">
                      {selectedSns.length > 0 ? (
                        <div className="flex flex-wrap gap-1">
                          {selectedSns.map((it) => (
                            <span key={it.id} className="rounded bg-blue-50 px-1.5 py-0.5 font-mono text-xs text-blue-700">
                              {it.serial_number || `#${it.id}`}
                            </span>
                          ))}
                        </div>
                      ) : (
                        <span className="text-xs text-gray-400">-</span>
                      )}
                    </td>
                    <td className="px-4 py-3 font-medium">{d.quantity}</td>
                  </tr>
                )})}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

function InfoCard({ icon: Icon, label, value, sub }) {
  return (
    <div className="rounded-lg border border-gray-200 bg-white p-4">
      <div className="mb-2 flex items-center gap-2">
        <Icon className="h-4 w-4 text-gray-400" />
        <p className="text-xs font-medium uppercase text-gray-500">{label}</p>
      </div>
      <p className="text-sm font-medium text-slate-700">{value || "-"}</p>
      {sub && <p className="mt-1 text-xs text-gray-400">{sub}</p>}
    </div>
  );
}