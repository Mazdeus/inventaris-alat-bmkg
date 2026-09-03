import { useState, useRef, useMemo } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { returnsApi } from "@/api/returns";
import { officersApi } from "@/api/officers";
import DataTable from "@/components/ui/DataTable";
import ExportButton from "@/components/ui/ExportButton";
import PageHeader from "@/components/ui/PageHeader";
import { ConfirmDialog } from "@/components/ui/ConfirmDialog";
import { formatDate } from "@/lib/formatters";
import { toast } from "sonner";
import { RotateCcw, Eye, Clock, FileDown, FileUp, Trash2, Pencil } from "lucide-react";

export default function ReturnListPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { isAuthenticated, isAdmin } = useAuth();
  const [page, setPage] = useState(1);
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const uploadRefs = useRef({});
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [editTarget, setEditTarget] = useState(null);
  const [editDate, setEditDate] = useState("");
  const [editOfficer, setEditOfficer] = useState("");

  const { data, isLoading, isError } = useQuery({
    queryKey: ["returns", page, startDate, endDate],
    queryFn: () =>
      returnsApi.getReturns({ page, size: 10, start_date: startDate || undefined, end_date: endDate || undefined }),
    keepPreviousData: true,
  });

  const { data: officersRes } = useQuery({
    queryKey: ["officers", "all"],
    queryFn: () => officersApi.getOfficers({ size: 100 }),
    staleTime: 2 * 60_000,
  });

  const returns = data?.data?.data || [];
  const meta = data?.data?.meta;
  const officers = officersRes?.data?.data || [];

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

  const editMutation = useMutation({
    mutationFn: ({ id, data }) => returnsApi.updateReturn(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["returns"] });
      setEditTarget(null);
      toast.success("Pengembalian berhasil diperbarui.");
    },
    onError: (err) => {
      toast.error(err?.response?.data?.detail || "Gagal memperbarui pengembalian");
    },
  });

  function openEdit(r) {
    setEditTarget(r);
    setEditDate(r.return_date || "");
    setEditOfficer(r.received_by ? String(r.received_by) : "");
  }

  function submitEdit() {
    if (!editTarget) return;
    editMutation.mutate({
      id: editTarget.id,
      data: {
        return_date: editDate || undefined,
        received_by: editOfficer ? Number(editOfficer) : undefined,
      },
    });
  }

  const statusColors = {
    Pending: "inline-flex items-center rounded-full bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-800",
    Completed: "inline-flex items-center rounded-full bg-emerald-100 px-2 py-0.5 text-xs font-medium text-emerald-800",
    Cancelled: "inline-flex items-center rounded-full bg-red-100 px-2 py-0.5 text-xs font-medium text-red-800",
  };

  /** Unduh template dokumen pengembalian */
  function handleDownloadDoc(id) {
    returnsApi.downloadDocument(id).then((res) => {
      const blob = new Blob([res.data], { type: "application/pdf" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `pengembalian_${id}.pdf`;
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
    { key: "daily_sequence", header: "No.", render: (r) => <span className="text-xs text-gray-500">{r.daily_sequence ?? "-"}</span> },
    { key: "transaction_number", header: "No. Transaksi", render: (r) => <span className="font-mono text-xs font-medium text-slate-700">{r.transaction_number || `#${r.id}`}</span> },
    { key: "borrow_transaction_number", header: "No. Pinjam", render: (r) => <span className="font-mono text-xs font-semibold text-blue-700">{r.borrow_transaction_number || (r.borrow_transaction_id ? `#${r.borrow_transaction_id}` : "-")}</span> },
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
    { key: "total_items", header: "Jumlah Barang", render: (r) => <span className="font-medium">{r.total_items ?? 0}</span> },
    { key: "actions", header: "Aksi", render: (r) => (
       <div className="flex gap-1">
         <button onClick={(e) => { e.stopPropagation(); navigate(`/returns/${r.id}`); }}
           className="rounded-md p-1 text-gray-500 hover:bg-gray-100" title="Detail">
           <Eye className="h-4 w-4" />
         </button>
         {/* Unduh & Upload dokumen — hanya untuk Menunggu */}
          {r.status === "Pending" && (
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
          {/* Edit — hanya status Menunggu */}
          {isAdmin && r.status === "Pending" && (
            <button onClick={(e) => { e.stopPropagation(); openEdit(r); }}
              className="rounded-md p-1 text-blue-600 hover:bg-blue-50" title="Ubah Pengembalian">
              <Pencil className="h-4 w-4" />
            </button>
          )}
          {/* Hapus — hanya status Menunggu */}
          {isAdmin && r.status === "Pending" && (
            <button onClick={(e) => { e.stopPropagation(); setDeleteTarget(r); }}
              className="rounded-md p-1 text-red-600 hover:bg-red-50" title="Hapus Pengembalian">
              <Trash2 className="h-4 w-4" />
            </button>
          )}
       </div>
     )},
  ];

  // Data export: satu baris per komponen/unit dalam pengembalian.
  const exportRows = useMemo(() => {
    const rows = [];
    (returns || []).forEach((r) => {
      const details = r.details || [];
      const base = {
        id: `#${r.id}`,
        transaction: `#${r.borrow_transaction_id}`,
        borrower_name: r.borrower_name || "-",
        received_by: r.officer_name || "-",
        return_date: `${formatDate(r.return_date)}${r.is_late ? ` (Terlambat ${r.days_late}h)` : ''}`,
        status: r.status || "-",
      };
      if (details.length === 0) {
        rows.push({ ...base, item_name: "-", brand: "-", model: "-", quantity: r.total_items ?? 0, serial_number: "-" });
      } else {
        details.forEach((d) => {
          const sns = (d.items || []).map((it) => it.serial_number || "-");
          rows.push({
            ...base,
            item_name: d.component?.item_name || "-",
            brand: d.component?.brand || "-",
            model: d.component?.model || "-",
            quantity: d.quantity ?? 0,
            serial_number: sns.length ? sns.join("\n") : "-",
          });
        });
      }
    });
    return rows;
  }, [returns]);

  const exportColumns = [
    { key: "id", header: "ID" },
    { key: "transaction", header: "Transaksi" },
    { key: "borrower_name", header: "Peminjam" },
    { key: "received_by", header: "Diterima Oleh" },
    { key: "return_date", header: "Tgl Kembali" },
    { key: "status", header: "Status" },
    { key: "item_name", header: "Nama Barang" },
    { key: "brand", header: "Merek" },
    { key: "model", header: "Model" },
    { key: "quantity", header: "Jumlah" },
    { key: "serial_number", header: "Serial Number" },
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
          <ExportButton data={exportRows} columns={exportColumns}
            filename={`Laporan_Pengembalian_${startDate || 'all'}_${endDate || 'all'}`}
            type="pdf" title="Laporan Pengembalian BMKG" />
          <ExportButton data={exportRows} columns={exportColumns}
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
        requirePassword
      />

      {/* Modal edit pengembalian */}
      {editTarget && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" onClick={() => setEditTarget(null)}>
          <div className="w-full max-w-md rounded-lg bg-white p-6 shadow-xl" onClick={(e) => e.stopPropagation()}>
            <h3 className="text-lg font-semibold text-slate-800">Edit Pengembalian #{editTarget.id}</h3>
            <div className="mt-4 space-y-3">
              <div>
                <label className="mb-1 block text-sm font-medium text-gray-700">Tanggal Kembali</label>
                <input type="date" value={editDate} onChange={(e) => setEditDate(e.target.value)}
                  className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-slate-400" />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium text-gray-700">Petugas Penerima</label>
                <select value={editOfficer} onChange={(e) => setEditOfficer(e.target.value)}
                  className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-slate-400">
                  <option value="">Pilih petugas...</option>
                  {officers.map((o) => (
                    <option key={o.id} value={o.id}>{o.officer_name}</option>
                  ))}
                </select>
              </div>
              {editMutation.isError && (
                <p className="text-xs text-red-600">{editMutation.error?.response?.data?.detail || "Gagal memperbarui"}</p>
              )}
            </div>
            <div className="mt-4 flex justify-end gap-3">
              <button onClick={() => setEditTarget(null)} className="rounded-md border border-gray-300 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50">Batal</button>
              <button onClick={submitEdit} disabled={editMutation.isPending}
                className="rounded-md bg-slate-800 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700 disabled:opacity-60">
                {editMutation.isPending ? "Menyimpan..." : "Simpan"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
