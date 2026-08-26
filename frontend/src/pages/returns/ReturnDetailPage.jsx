import { useState, useRef } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { returnsApi } from "@/api/returns";
import { useAuth } from "@/contexts/AuthContext";
import PageHeader from "@/components/ui/PageHeader";
import { ConfirmDialog } from "@/components/ui/ConfirmDialog";
import { formatDate } from "@/lib/formatters";
import { ArrowLeft, Clock, Calendar, User, FileDown, FileUp, Check, X, Loader2 } from "lucide-react";
import { STATUS_LABELS } from "@/lib/constants";

export default function ReturnDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { isAdmin } = useAuth();
  const fileInputRef = useRef(null);

  const [verifyOpen, setVerifyOpen] = useState(false);
  const [rejectOpen, setRejectOpen] = useState(false);

  const { data, isLoading, isError } = useQuery({
    queryKey: ["return", id],
    queryFn: () => returnsApi.getReturn(Number(id)),
    enabled: !!id,
  });

  const ret = data?.data?.data;

  // Download document
  function handleDownloadDoc() {
    returnsApi.downloadDocument(ret.id).then((res) => {
      const blob = new Blob([res.data], { type: "application/pdf" });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `pengembalian_${ret.id}.pdf`;
      a.click();
      window.URL.revokeObjectURL(url);
    }).catch(() => {});
  }

  // Upload document
  const uploadMut = useMutation({
    mutationFn: (file) => returnsApi.uploadDocument(ret.id, file),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["return", id] }),
  });

  function handleUploadFile(e) {
    const file = e.target.files?.[0];
    if (!file) return;
    uploadMut.mutate(file);
    e.target.value = "";
  }

  // Verify
  const verifyMut = useMutation({
    mutationFn: () => returnsApi.verifyReturn(ret.id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["return", id] });
      queryClient.invalidateQueries({ queryKey: ["returns"] });
      setVerifyOpen(false);
    },
  });

  // Reject
  const rejectMut = useMutation({
    mutationFn: () => returnsApi.rejectReturn(ret.id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["return", id] });
      queryClient.invalidateQueries({ queryKey: ["returns"] });
      setRejectOpen(false);
    },
  });

  const conditionColors = { Baik: "bg-emerald-100 text-emerald-800", Rusak: "bg-red-100 text-red-800" };
  const statusColors = { "Menunggu": "bg-amber-100 text-amber-800", "Selesai": "bg-emerald-100 text-emerald-800", "Dibatalkan": "bg-red-100 text-red-800" };

  if (isLoading) return <div className="space-y-4"><div className="h-6 w-40 animate-pulse rounded bg-gray-200" /><div className="h-40 animate-pulse rounded-lg bg-gray-200" /></div>;
  if (isError || !ret) return (
    <div className="rounded-lg border border-red-200 bg-red-50 p-6 text-center text-red-700">
      Gagal memuat data.
      <button onClick={() => navigate("/returns")} className="mt-2 block text-sm underline">Kembali</button>
    </div>
  );

  return (
    <div>
      <button onClick={() => navigate("/returns")} className="mb-4 flex items-center gap-1 text-sm text-gray-500 hover:text-slate-700"><ArrowLeft className="h-4 w-4" /> Kembali</button>
      <PageHeader title={`Pengembalian ${ret.transaction_number || `#${ret.id}`}`} description={`Transaksi #${ret.borrow_transaction_id} · ${ret.borrower_name}`} />

      {/* Status */}
      <div className="mb-4">
        <p className="mb-1 text-xs text-gray-500">Status Pengembalian</p>
        <span className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-medium ${statusColors[ret.status] || "bg-gray-100 text-gray-600"}`}>
          {ret.status}
        </span>
      </div>

      {/* Late indicator */}
      {ret.is_late && (
        <div className="mb-6 rounded-lg border border-red-200 bg-red-50 p-4">
          <div className="flex items-center gap-2">
            <Clock className="h-4 w-4 text-red-500" />
            <p className="text-sm font-semibold text-red-700">
              Terlambat {ret.days_late} hari · Rencana kembali: {formatDate(ret.expected_return_date)}
            </p>
          </div>
          {ret.late_reason && (
            <p className="mt-2 text-sm text-red-600">
              <span className="font-medium">Alasan:</span> {ret.late_reason}
            </p>
          )}
        </div>
      )}

      {/* Extension info */}
      {ret?.extension?.status === "Disetujui" && (
        <div className="mb-6 rounded-lg border border-amber-200 bg-amber-50 p-4">
          <div className="flex items-center gap-2">
            <Clock className="h-4 w-4 text-amber-500" />
            <p className="text-sm font-semibold text-amber-700">
              Peminjaman diperpanjang · Kembali: {ret.extension.new_date || "-"}
            </p>
          </div>
          {ret.extension.reason && (
            <p className="mt-1 text-sm text-amber-600">
              <span className="font-medium">Alasan:</span> {ret.extension.reason}
            </p>
          )}
        </div>
      )}

      {/* Info cards */}
      <div className="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <InfoCard icon={User} label="Diterima Oleh" value={ret.officer_name || "-"} />
        <InfoCard icon={Calendar} label="Tanggal Pinjam" value={formatDate(ret.borrow_date)} />
        <InfoCard icon={Calendar} label="Rencana Kembali" value={formatDate(ret.expected_return_date)} />
        <InfoCard icon={Calendar} label="Tanggal Kembali" value={formatDate(ret.return_date)} />
      </div>

      {/* Foto Dokumentasi */}
      {ret.photo && (
        <div className="mb-6 rounded-lg border border-gray-200 bg-white p-4">
          <p className="mb-2 text-xs font-medium uppercase text-gray-500">Foto Dokumentasi Pengembalian</p>
          <img
            src={`/uploads/${ret.photo}`}
            alt="Foto pengembalian"
            className="max-h-64 rounded-md object-cover"
            onError={(e) => { e.target.style.display = "none"; }}
          />
        </div>
      )}

      {/* Section Dokumen */}
      <div className="mb-6 rounded-lg border border-gray-200 bg-white p-4">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-semibold text-gray-700 flex items-center gap-1.5">
              <FileDown className="h-4 w-4 text-gray-400" /> Dokumen Pengembalian
            </p>
            <p className="mt-1 text-xs text-gray-500">
              {ret.signed_document
                ? "Dokumen sudah ditandatangani dan diupload."
                : "Unduh, tanda tangani, lalu unggah kembali dokumen yang sudah ditandatangani."}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <button onClick={handleDownloadDoc}
              className="flex items-center gap-1 rounded-md border border-gray-300 bg-white px-3 py-2 text-xs text-gray-700 hover:bg-gray-50">
              <FileDown className="h-3.5 w-3.5" /> Unduh Dokumen
            </button>
            {/* Upload hanya untuk Menunggu */}
            {ret.status === "Menunggu" && (
            <label className="flex cursor-pointer items-center gap-1 rounded-md bg-slate-800 px-3 py-2 text-xs font-medium text-white hover:bg-slate-700">
              <FileUp className="h-3.5 w-3.5" /> Unggah Tertandatangan
              <input type="file" ref={fileInputRef} accept=".pdf,.png,.jpg,.jpeg"
                onChange={handleUploadFile} className="hidden" />
            </label>
            )}
          </div>
        </div>
        {uploadMut.isPending && (
          <p className="mt-2 flex items-center gap-1 text-xs text-blue-600"><Loader2 className="h-3 w-3 animate-spin" /> Mengunggah...</p>
        )}
        {uploadMut.isError && (
          <p className="mt-2 text-xs text-red-600">Gagal mengunggah: {uploadMut.error?.response?.data?.detail || "Error"}</p>
        )}
        {ret.signed_document && (
          <div className="mt-3">
            <p className="text-xs font-medium text-emerald-600">✓ Dokumen tertandatangan sudah diunggah</p>
            <a href={`/uploads/${ret.signed_document}`} target="_blank" rel="noopener noreferrer"
              className="mt-1 inline-block text-xs text-blue-600 underline hover:text-blue-800">
              Lihat Dokumen
            </a>
          </div>
        )}
      </div>

      {/* Admin: Verifikasi */}
      {isAdmin && ret.status === "Menunggu" && (
        <div className="mb-6 rounded-lg border border-gray-200 bg-white p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-semibold text-gray-700">Verifikasi</p>
              <p className="mt-1 text-xs text-gray-500">Pastikan dokumen sudah benar sebelum memverifikasi.</p>
            </div>
            <div className="flex items-center gap-2">
              {!ret.signed_document && (
                <p className="text-xs text-amber-600">Dokumen harus diunggah terlebih dahulu</p>
              )}
              <button
                onClick={() => setVerifyOpen(true)}
                disabled={!ret.signed_document}
                className="flex items-center gap-1 rounded-md bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700 disabled:cursor-not-allowed disabled:opacity-50"
              >
                <Check className="h-4 w-4" /> Setujui
              </button>
              <button
                onClick={() => setRejectOpen(true)}
                className="flex items-center gap-1 rounded-md bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700"
              >
                <X className="h-4 w-4" /> Tolak
              </button>
            </div>
          </div>
        </div>
      )}

      <ConfirmDialog open={verifyOpen} onOpenChange={setVerifyOpen}
        title="Setujui Pengembalian" message="Setujui pengembalian ini? Status barang akan diubah dan peminjaman ditandai Dikembalikan."
        onConfirm={() => verifyMut.mutate()}
        confirmLabel="Setujui" variant="default" />

      <ConfirmDialog open={rejectOpen} onOpenChange={setRejectOpen}
        title="Tolak Pengembalian" message="Tolak pengembalian ini? Status pengembalian akan menjadi Dibatalkan dan peminjaman tetap Dipinjam."
        onConfirm={() => rejectMut.mutate()}
        confirmLabel="Tolak" variant="danger" />

      {/* Detail per komponen & SN */}
      <div className="rounded-lg border border-gray-200 bg-white">
        <div className="border-b border-gray-100 px-4 py-3"><h3 className="text-sm font-semibold text-gray-700">Detail Barang Dikembalikan</h3></div>
        {!ret.details?.length ? <p className="p-8 text-center text-sm text-gray-400">Tidak ada detail</p> : (
          <div className="overflow-x-auto">
            {ret.details.map((d) => (
              <div key={d.id} className="mb-2 last:mb-0">
                <div className="border-b border-gray-100 bg-gray-50 px-4 py-2">
                  <p className="text-sm font-medium text-slate-700">
                    {d.component?.item_name || "-"} · <span className="text-xs text-gray-500">{d.quantity} barang</span>
                  </p>
                </div>
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-gray-100 text-left">
                      <th className="px-4 py-2 font-semibold text-gray-600">Nomor Seri</th>
                      <th className="px-4 py-2 font-semibold text-gray-600">Kondisi</th>
                      <th className="px-4 py-2 font-semibold text-gray-600">Status Setelah</th>
                      <th className="px-4 py-2 font-semibold text-gray-600">Catatan</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {d.items.map((it) => (
                      <tr key={it.id}>
                        <td className="px-4 py-2">
                          <span className="font-mono text-xs font-medium text-slate-800">{it.serial_number || `#${it.inventory_item_id}`}</span>
                        </td>
                        <td className="px-4 py-2">
                          <span className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${conditionColors[it.condition] || "bg-gray-100 text-gray-600"}`}>{it.condition}</span>
                        </td>
                        <td className="px-4 py-2 text-xs text-gray-600">{STATUS_LABELS[it.status_after] || it.status_after || "-"}</td>
                        <td className="px-4 py-2 text-xs text-gray-600">{it.notes || "-"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ))}
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
