import { useState, useRef } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { returnsApi } from "@/api/returns";
import DataTable from "@/components/ui/DataTable";
import ExportButton from "@/components/ui/ExportButton";
import PageHeader from "@/components/ui/PageHeader";
import { ConfirmDialog } from "@/components/ui/ConfirmDialog";
import { formatDate } from "@/lib/formatters";
import { toast } from "sonner";
import { RotateCcw, Eye, Clock, FileDown, FileUp, Trash2 } from "lucide-react";

export default function ReturnListPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { isAuthenticated, isAdmin } = useAuth();
  const [page, setPage] = useState(1);
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const uploadRefs = useRef({});
  const [deleteTarget, setDeleteTarget] = useState(null);

  const { data, isLoading, isError } = useQuery({
    queryKey: ["returns", page, startDate, endDate],
    queryFn: () =>
      returnsApi.getReturns({ page, size: 10, start_date: startDate || undefined, end_date: endDate || undefined }),
    keepPreviousData: true,
  });

  const returns = data?.data?.data || [];
  const meta = data?.data?.meta;

  const deleteMutation = useMutation({
    mutationFn: (id) => returnsApi.deleteReturn(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["returns"] });
      queryClient.invalidateQueries({ queryKey: ["transactions"] });
      setDeleteTarget(null);
      toast.success("Pengembalian berhasil dihapus.");
    },
    onError: (err) => {
      toast.error(err?.response?.data?.detail || "Gagal menghapus pengembalian");
    },
  });

  const statusColors = {
    "Menunggu Verifikasi": "inline-flex items-center rounded-full bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-800",
    "Selesai": "inline-flex items-center rounded-full bg-emerald-100 px-2 py-0.5 text-xs font-medium text-emerald-800",
    "Dibatalkan": "inline-flex items-center rounded-full bg-red-100 px-2 py-0.5 text-xs font-medium text-red-800",
  };

  /** Unduh template dokumen pengembalian */
  function handleDownloadDoc(id) {
    returnsApi.downloadDocument(id).then((res) => {
      const blob = new Blob([res.data], { type: "text/plain" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `pengembalian_${id}.txt`;
      a.click();
      URL.revokeObjectURL(url);
    }).catch(() => {});
  }

  /** Upload dokumen tertandatangan */
  function handleUploadFile(e, id) {
    const file = e.target.files?.[0];
    if (!file) return;
    returnsApi.uploadDocument(id, file).then(() => {
      queryClient.invalidateQueries({ queryKey: ["returns"] });
    }).catch(() => {});
  }

  /** Trigger file input untuk upload */
  function handleUploadClick(id) {
    uploadRefs.current[id]?.click();
  }

  const columns = [
    { key: "id", header: "ID", render: (r) => <span className="text-xs text-gray-500">#{r.id}</span> },
    { key: "borrow_transaction_id", header: "Transaksi", render: (r) => <span className="text-sm">#{r.borrow_transaction_id}</span> },
    { key: "borrower_name", header: "Peminjam", render: (r) => <span className="font-medium">{r.borrower_name || "-"}</span> },
    { key: "received_by", header: "Diterima Oleh", render: (r) => r.officer_name || "-" },
    { key: "return_date", header: "Tgl Kembali", render: (r) => (
      <div className="flex items-center gap-1.5">
        <span>{formatDate(r.return_date)}</span>
        {r.is_late && (
          <span className="inline-flex items-center gap-0.5 rounded-full bg-red-100 px-1.5 py-0.5 text-xs font-medium text-red-700" title={`Terlambat ${r.days_late} hari`}>
            <Clock className="h-3 w-3" /> {r.days_late}h
          </span>
        )}
      </div>
    )},
    { key: "status", header: "Status", render: (r) => (
      <span className={statusColors[r.status] || "inline-flex items-center rounded-full bg-gray-100 px-2 py-0.5 text-xs font-medium text-gray-800"}>
        {r.status || "-"}
      </span>
    )},
    { key: "items_count", header: "Barang", render: (r) => <span className="font-medium">{r.items_count ?? 0}</span> },
    { key: "actions", header: "Aksi", render: (r) => (
       <div className="flex gap-1">
         <button onClick={(e) => { e.stopPropagation(); navigate(`/returns/${r.id}`); }}
           className="rounded-md p-1 text-gray-500 hover:bg-gray-100" title="Detail">
           <Eye className="h-4 w-4" />
         </button>
         {/* Unduh & Upload dokumen — hanya untuk Menunggu Verifikasi */}
         {r.status === "Menunggu Verifikasi" && (
           <>
             <button onClick={(e) => { e.stopPropagation(); handleDownloadDoc(r.id); }}
               className="rounded-md p-1 text-blue-600 hover:bg-blue-50" title="Unduh Dokumen">
               <FileDown className="h-4 w-4" />
             </button>
             <button onClick={(e) => { e.stopPropagation(); handleUploadClick(r.id); }}
               className="rounded-md p-1 text-purple-600 hover:bg-purple-50" title="Unggah Dokumen Tertandatangan">
               <FileUp className="h-4 w-4" />
               <input type="file" ref={(el) => { uploadRefs.current[r.id] = el; }}
                 onChange={(e) => handleUploadFile(e, r.id)}
                 accept=".pdf,.png,.jpg,.jpeg" className="hidden" />
             </button>
           </>
         )}
         {r.signed_document && (
            <span className="rounded-md px-1 py-0.5 text-xs text-emerald-600 bg-emerald-50">✓</span>
          )}
          {/* Hapus — hanya status Menunggu Verifikasi */}
          {isAdmin && r.status === "Menunggu Verifikasi" && (
            <button onClick={(e) => { e.stopPropagation(); setDeleteTarget(r); }}
              className="rounded-md p-1 text-red-600 hover:bg-red-50" title="Hapus Pengembalian">
              <Trash2 className="h-4 w-4" />
            </button>
          )}
       </div>
     )},
  ];

  const exportColumns = [
    { key: "id", header: "ID", render: (r) => `#${r.id}` },
    { key: "borrow_transaction_id", header: "Transaksi", render: (r) => `#${r.borrow_transaction_id}` },
    { key: "borrower_name", header: "Peminjam", render: (r) => r.borrower_name || "-" },
    { key: "received_by", header: "Diterima Oleh", render: (r) => r.officer_name || "-" },
    { key: "return_date", header: "Tgl Kembali", render: (r) => `${formatDate(r.return_date)}${r.is_late ? ` (Terlambat ${r.days_late}h)` : ''}` },
    { key: "status", header: "Status", render: (r) => r.status || "-" },
    { key: "items_count", header: "Barang", render: (r) => r.items_count ?? 0 },
  ];

  return (
    <div>
      <PageHeader title="Pengembalian" description="Riwayat pengembalian inventaris" />
      {isError && <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">Gagal memuat data.</div>}
      <div className="mb-4 flex flex-wrap items-center gap-3">
        <input type="date" value={startDate} onChange={(e) => { setStartDate(e.target.value); setPage(1); }}
          className="rounded-md border border-gray-300 px-2 py-1 text-xs text-gray-600" />
        <span className="text-xs text-gray-400">s/d</span>
        <input type="date" value={endDate} onChange={(e) => { setEndDate(e.target.value); setPage(1); }}
          className="rounded-md border border-gray-300 px-2 py-1 text-xs text-gray-600" />
        <div className="ml-auto flex items-center gap-2">
          <ExportButton data={returns} columns={exportColumns}
            filename={`Laporan_Pengembalian_${startDate || 'all'}_${endDate || 'all'}`}
            type="pdf" title="Laporan Pengembalian BMKG" />
          <ExportButton data={returns} columns={exportColumns}
            filename={`Laporan_Pengembalian_${startDate || 'all'}_${endDate || 'all'}`}
            type="excel" />
        </div>
        {isAuthenticated && (
          <button onClick={() => navigate("/returns/new")}
            className="flex items-center gap-1 rounded-md bg-slate-800 px-3 py-2 text-sm font-medium text-white hover:bg-slate-700">
            <RotateCcw className="h-4 w-4" /> Proses Pengembalian
          </button>
        )}
      </div>
      <DataTable columns={columns} data={returns} loading={isLoading} page={meta?.page} totalPages={meta?.total_pages}
        onPageChange={setPage}
        emptyTitle="Belum ada pengembalian" emptyMessage="Klik 'Proses Pengembalian' untuk mencatat pengembalian." />

      <ConfirmDialog
        open={!!deleteTarget}
        onOpenChange={() => setDeleteTarget(null)}
        title="Hapus Pengembalian"
        message={`Anda akan menghapus pengembalian #${deleteTarget?.id}. Peminjaman #${deleteTarget?.borrow_transaction_id} dan status barang tidak berubah. Lanjutkan?`}
        onConfirm={() => deleteTarget && deleteMutation.mutate(deleteTarget.id)}
        confirmLabel="Hapus"
        variant="danger"
      />
    </div>
  );
}
