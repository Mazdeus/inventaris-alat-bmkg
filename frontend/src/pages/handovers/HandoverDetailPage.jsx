import { useState, useRef } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { handoversApi } from "@/api/handovers";
import { useAuth } from "@/contexts/AuthContext";
import { STATUS_LABELS } from "@/lib/constants";
import PageHeader from "@/components/ui/PageHeader";
import { ArrowLeft, Download, Upload, Loader2, CheckCircle, XCircle } from "lucide-react";
import { toast } from "sonner";

export default function HandoverDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { isAdmin } = useAuth();
  const fileInputRef = useRef(null);
  const [uploading, setUploading] = useState(false);

  const { data, isLoading, isError } = useQuery({
    queryKey: ["handover", id],
    queryFn: () => handoversApi.getHandover(Number(id)),
    enabled: !!id,
  });

  const h = data?.data?.data;

  // Complete mutation
  const completeMutation = useMutation({
    mutationFn: () => handoversApi.completeHandover(Number(id)),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["handover", id] });
      queryClient.invalidateQueries({ queryKey: ["handovers"] });
      toast.success("Pelimpahan berhasil diselesaikan");
    },
    onError: (err) => toast.error(err?.response?.data?.detail || "Gagal menyelesaikan pelimpahan"),
  });

  // Cancel mutation
  const cancelMutation = useMutation({
    mutationFn: () => handoversApi.cancelHandover(Number(id)),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["handover", id] });
      queryClient.invalidateQueries({ queryKey: ["handovers"] });
      toast.success("Pelimpahan dibatalkan");
    },
    onError: (err) => toast.error(err?.response?.data?.detail || "Gagal membatalkan pelimpahan"),
  });

  function handleDownloadDoc() {
    handoversApi.downloadDocument(Number(id)).then((res) => {
      const blob = new Blob([res.data], { type: "application/pdf" });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `BAST_Pelimpahan_${id}.pdf`;
      a.click();
      window.URL.revokeObjectURL(url);
    }).catch(() => toast.error("Gagal mengunduh dokumen"));
  }


  function handleUploadDoc(e) {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    handoversApi.uploadDocument(Number(id), file).then((res) => {
      // Update cache langsung dari response agar dokumen langsung tampil
      queryClient.setQueryData(["handover", id], (old) => {
        if (old) return { ...old, data: { ...old.data, data: res.data.data } };
        return old;
      });
      queryClient.invalidateQueries({ queryKey: ["handovers"] });
      toast.success("Dokumen berhasil diupload");
    }).catch((err) => toast.error(err?.response?.data?.detail || "Gagal upload dokumen"))
    .finally(() => setUploading(false));
    if (fileInputRef.current) fileInputRef.current.value = "";
  }

  if (isLoading) return <div className="animate-pulse h-48 rounded-lg bg-gray-200" />;
  if (isError || !h) return (
    <div className="rounded-lg border border-red-200 bg-red-50 p-6 text-center text-red-700">
      Gagal memuat data. <button onClick={() => navigate("/handovers")} className="mt-2 block text-sm underline">Kembali</button>
    </div>
  );

  const isDraft = h.status === "Draft";
  const isCompleted = h.status === "Transferred";

  return (
    <div>
      <button onClick={() => navigate("/handovers")} className="mb-4 flex items-center gap-1 text-sm text-gray-500 hover:text-slate-700">
        <ArrowLeft className="h-4 w-4" /> Kembali
      </button>
      <PageHeader title={`Pelimpahan #${h.id}`} description={`Ke UPT: ${h.upt_receiver}`} />

      {/* Info */}
      <div className="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <InfoCard label="UPT Penerima" value={h.upt_receiver} />
        <InfoCard label="Tanggal Pelimpahan" value={h.handover_date} />
        <InfoCard label="Petugas" value={h.officer_name || "-"} />
        <InfoCard label="Status" value={<span className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${
          h.status === "Transferred" ? "bg-emerald-100 text-emerald-800" :
          h.status === "Draft" ? "bg-yellow-100 text-yellow-800" :
          "bg-red-100 text-red-800"
        }`}>{STATUS_LABELS[h.status] || h.status}</span>} />
      </div>

      {/* Catatan */}
      {h.notes && (
        <div className="mb-4 rounded-lg border border-gray-200 bg-white p-4">
          <p className="mb-1 text-xs font-medium text-gray-500">Catatan</p>
          <p className="text-sm text-gray-700">{h.notes}</p>
        </div>
      )}

      {/* Daftar Barang */}
      <div className="mb-6 rounded-lg border border-gray-200 bg-white">
        <div className="border-b px-4 py-3">
          <h3 className="text-sm font-semibold text-gray-700">Barang yang Dilimpahkan ({h.items?.length || 0})</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b bg-gray-50 text-left">
                <th className="px-4 py-2 font-semibold text-gray-600">#</th>
                <th className="px-4 py-2 font-semibold text-gray-600">Nomor Seri</th>
                <th className="px-4 py-2 font-semibold text-gray-600">Unit</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {h.items?.map((it, idx) => (
                <tr key={it.id}>
                  <td className="px-4 py-2 text-gray-500">{idx + 1}</td>
                  <td className="px-4 py-2"><span className="font-mono text-xs">{it.serial_number || "-"}</span></td>
                  <td className="px-4 py-2 text-gray-700">{it.component_name}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Dokumen */}
      <div className="rounded-lg border border-gray-200 bg-white p-4">
        <h3 className="mb-3 text-sm font-semibold text-gray-700">Dokumen Pelimpahan</h3>
        <p className="mb-3 text-xs text-gray-500">
          {h.signed_document
            ? "Dokumen sudah ditandatangani dan diupload."
            : "Unduh, tanda tangani, lalu unggah kembali dokumen yang sudah ditandatangani."}
        </p>
        <div className="flex flex-wrap items-center gap-3">
          <button onClick={handleDownloadDoc}
            className="flex items-center gap-1 rounded-md border border-gray-300 px-3 py-2 text-sm text-gray-700 hover:bg-gray-50">
            <Download className="h-4 w-4" /> Unduh Dokumen
          </button>
          {isDraft && (
            <label className="flex cursor-pointer items-center gap-1 rounded-md bg-slate-800 px-3 py-2 text-sm font-medium text-white hover:bg-slate-700">
              <Upload className="h-4 w-4" /> {uploading ? "Mengunggah..." : "Unggah Tertandatangan"}
              <input type="file" ref={fileInputRef} accept=".pdf,.png,.jpg,.jpeg"
                onChange={handleUploadDoc} className="hidden" disabled={uploading} />
            </label>
          )}
        </div>
        {h.signed_document && (
          <div className="mt-3 flex items-center gap-2">
            <span className="text-xs text-emerald-600 font-medium">✓ Dokumen sudah diunggah</span>
            <a href={`/uploads/${h.signed_document}`} target="_blank" rel="noopener noreferrer"
              className="text-xs text-blue-600 hover:underline">Lihat Dokumen</a>
          </div>
        )}
      </div>

      {/* Aksi: Complete/Cancel (Admin, hanya saat Draft) */}
      {isAdmin && isDraft && (
        <div className="mt-6">
          {!h.signed_document && (
            <p className="mb-2 text-xs text-amber-600">Dokumen harus diunggah terlebih dahulu sebelum melimpahkan</p>
          )}
          <div className="flex flex-wrap gap-3">
          <button onClick={() => completeMutation.mutate()} disabled={completeMutation.isPending || !h.signed_document}
            className="flex items-center gap-1 rounded-md bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed">
            {completeMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <CheckCircle className="h-4 w-4" />}
            Dilimpahkan
          </button>
          <button onClick={() => cancelMutation.mutate()} disabled={cancelMutation.isPending}
            className="flex items-center gap-1 rounded-md bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700 disabled:opacity-60">
            {cancelMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <XCircle className="h-4 w-4" />}
            Batalkan
          </button>
          </div>
        </div>
      )}
    </div>
  );
}

function InfoCard({ label, value }) {
  return (
    <div className="rounded-lg border border-gray-200 bg-white p-4">
      <p className="mb-1 text-xs font-medium text-gray-500">{label}</p>
      {typeof value === "string" ? (
        <p className="text-sm font-medium text-slate-700">{value}</p>
      ) : value}
    </div>
  );
}
