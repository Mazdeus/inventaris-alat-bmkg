import { useState, useRef } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { borrowApi } from "@/api/borrow";
import DataTable from "@/components/ui/DataTable";
import ExportButton from "@/components/ui/ExportButton";
import PageHeader from "@/components/ui/PageHeader";
import FilterBar from "@/components/ui/FilterBar";
import StatusBadge from "@/components/ui/StatusBadge";
import { ConfirmDialog } from "@/components/ui/ConfirmDialog";
import { formatDate } from "@/lib/formatters";
import { toast } from "sonner";
import { Plus, Eye, Ban, FileDown, FileUp, Trash2 } from "lucide-react";

/**
 * Halaman daftar transaksi peminjaman.
 * Admin: bisa cancel / hapus per transaksi. Semua user: bisa lihat & tambah.
 * Approve/Reject dipindahkan ke halaman detail.
 */
export default function TransactionListPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { isAdmin, isAuthenticated } = useAuth();

  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [filterStatus, setFilterStatus] = useState(null);
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");

  // Confirm dialogs
  const [cancelId, setCancelId] = useState(null);
  const [deleteTarget, setDeleteTarget] = useState(null);

  // Document upload
  const uploadRefs = useRef({});

  const { data, isLoading, isError } = useQuery({
    queryKey: ["transactions", page, search, filterStatus, startDate, endDate],
    queryFn: () =>
      borrowApi.getTransactions({
        page, size: 10,
        borrower_name: search || undefined,
        status: filterStatus || undefined,
        start_date: startDate || undefined,
        end_date: endDate || undefined,
      }),
    keepPreviousData: true,
  });

  const transactions = data?.data?.data || [];
  const meta = data?.data?.meta;

  // Mutations
  const cancelMutation = useMutation({
    mutationFn: (id) => borrowApi.cancel(id),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ["transactions"] }); setCancelId(null); },
  });

  const deleteMutation = useMutation({
    mutationFn: (id) => borrowApi.bulkDelete([id]),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["transactions"] });
      queryClient.invalidateQueries({ queryKey: ["returns"] });
      setDeleteTarget(null);
      toast.success("Transaksi peminjaman berhasil dihapus");
    },
    onError: (err) => {
      toast.error(err?.response?.data?.detail?.message || err?.response?.data?.detail || "Gagal menghapus transaksi");
    },
  });

  // Helper: upload dokumen hanya saat status Menunggu
  const canUploadDoc = (status) => status === "Menunggu";

  // Document download
  function handleDownloadDoc(id) {
    borrowApi.downloadDocument(id).then((res) => {
      const blob = new Blob([res.data], { type: "text/plain" });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `peminjaman_${id}.txt`;
      a.click();
      window.URL.revokeObjectURL(url);
    }).catch(() => {});
  }

  // Document upload (via hidden file input)
  function handleUploadClick(id) {
    uploadRefs.current[id]?.click();
  }

  function handleUploadFile(e, id) {
    const file = e.target.files?.[0];
    if (!file) return;
    borrowApi.uploadDocument(id, file).then(() => {
      queryClient.invalidateQueries({ queryKey: ["transactions"] });
    }).catch(() => {});
    e.target.value = "";
  }

  // Check if transaction is deletable
  const isDeletable = (status) => status === "Menunggu" || status === "Dibatalkan" || status === "Dikembalikan";

  const columns = [
    { key: "id", header: "ID", render: (row) => <span className="text-xs text-gray-500">#{row.id}</span> },
    {
      key: "borrower",
      header: "Peminjam",
      render: (row) => (
        <div>
          <p className="font-medium text-slate-800">{row.borrower?.borrower_name || "-"}</p>
          <p className="text-xs text-gray-400">{row.borrower?.borrower_type || "-"}</p>
        </div>
      ),
    },
    { key: "borrow_date", header: "Tgl Pinjam", render: (row) => formatDate(row.borrow_date) },
    { key: "expected_return_date", header: "Tgl Kembali", render: (row) => formatDate(row.expected_return_date) },
    { key: "items_count", header: "Barang", render: (row) => <span className="font-medium">{row.items_count ?? 0}</span> },
    { key: "status", header: "Status", render: (row) => <StatusBadge type="borrow" value={row.status} /> },
    {
      key: "actions",
      header: "Aksi",
      render: (row) => (
        <div className="flex gap-1">
          <button onClick={(e) => { e.stopPropagation(); navigate(`/borrow/transactions/${row.id}`); }}
            className="rounded-md p-1 text-gray-500 hover:bg-gray-100" title="Detail">
            <Eye className="h-4 w-4" />
          </button>
          {/* Download Document — selalu tersedia (publik) */}
          <button onClick={(e) => { e.stopPropagation(); handleDownloadDoc(row.id); }}
            className="rounded-md p-1 text-blue-600 hover:bg-blue-50" title="Unduh Dokumen">
            <FileDown className="h-4 w-4" />
          </button>
          {/* Upload Signed Document — hanya saat status Menunggu */}
          {canUploadDoc(row.status) && (
            <button onClick={(e) => { e.stopPropagation(); handleUploadClick(row.id); }}
              className="rounded-md p-1 text-purple-600 hover:bg-purple-50" title="Unggah Dokumen Tertandatangan">
              <FileUp className="h-4 w-4" />
              <input type="file" ref={(el) => { uploadRefs.current[row.id] = el; }}
                onChange={(e) => handleUploadFile(e, row.id)}
                accept=".pdf,.png,.jpg,.jpeg" className="hidden" />
            </button>
          )}
          {row.signed_document && (
            <span className="rounded-md px-1 py-0.5 text-xs text-emerald-600 bg-emerald-50">✓ Dokumen</span>
          )}
          {/* Admin: Cancel (Dipinjam) */}
          {isAdmin && row.status === "Dipinjam" && (
            <button onClick={(e) => { e.stopPropagation(); setCancelId(row.id); }}
              className="rounded-md p-1 text-orange-600 hover:bg-orange-50" title="Batalkan">
              <Ban className="h-4 w-4" />
            </button>
          )}
          {/* Admin: Hapus (Menunggu, Dibatalkan, Dikembalikan) */}
          {isAdmin && isDeletable(row.status) && (
            <button onClick={(e) => { e.stopPropagation(); setDeleteTarget(row); }}
              className="rounded-md p-1 text-red-600 hover:bg-red-50" title="Hapus">
              <Trash2 className="h-4 w-4" />
            </button>
          )}
        </div>
      ),
    },
  ];

  // Kolom untuk export (plain text)
  const exportColumns = [
    { key: "id", header: "ID", render: (row) => `#${row.id}` },
    { key: "borrower_name", header: "Peminjam", render: (row) => row.borrower?.borrower_name || "-" },
    { key: "borrower_type", header: "Tipe", render: (row) => row.borrower?.borrower_type || "-" },
    { key: "borrow_date", header: "Tgl Pinjam", render: (row) => formatDate(row.borrow_date) },
    { key: "expected_return_date", header: "Tgl Kembali", render: (row) => formatDate(row.expected_return_date) },
    { key: "items_count", header: "Barang", render: (row) => row.items_count ?? 0 },
    { key: "status", header: "Status", render: (row) => row.status },
    { key: "officer_name", header: "Petugas", render: (row) => row.officer_name || "-" },
  ];

  const filters = [
    {
      label: "Status", key: "status", value: filterStatus,
      onChange: (v) => { setFilterStatus(v || null); setPage(1); },
      options: [
        { value: "Menunggu", label: "Menunggu" },
        { value: "Dipinjam", label: "Dipinjam" },
        { value: "Dikembalikan", label: "Dikembalikan" },
        { value: "Dibatalkan", label: "Dibatalkan" },
      ],
    },
  ];

  return (
    <div>
      <PageHeader
        title="Peminjaman"
        description="Transaksi peminjaman inventaris"
        actions={
          isAuthenticated ? (
            <button onClick={() => navigate("/borrow/transactions/new")}
              className="flex items-center gap-1 rounded-md bg-slate-800 px-3 py-2 text-sm font-medium text-white hover:bg-slate-700">
              <Plus className="h-4 w-4" /> Peminjaman Baru
            </button>
          ) : null
        }
      />

      {isError && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          Gagal memuat data. Pastikan backend berjalan.
        </div>
      )}

      {/* Date filters + Export */}
      <div className="mb-4 flex flex-wrap items-center gap-3">
        <FilterBar filters={filters} />
        <div className="flex items-center gap-2">
          <input type="date" value={startDate} onChange={(e) => { setStartDate(e.target.value); setPage(1); }}
            className="rounded-md border border-gray-300 px-2 py-1 text-xs text-gray-600" />
          <span className="text-xs text-gray-400">s/d</span>
          <input type="date" value={endDate} onChange={(e) => { setEndDate(e.target.value); setPage(1); }}
            className="rounded-md border border-gray-300 px-2 py-1 text-xs text-gray-600" />
        </div>
        <div className="ml-auto flex items-center gap-2">
          <ExportButton data={transactions} columns={exportColumns}
            filename={`Laporan_Peminjaman_${startDate || 'all'}_${endDate || 'all'}`}
            type="pdf" title="Laporan Peminjaman BMKG" />
          <ExportButton data={transactions} columns={exportColumns}
            filename={`Laporan_Peminjaman_${startDate || 'all'}_${endDate || 'all'}`}
            type="excel" />
        </div>
      </div>

      <DataTable
        columns={columns} data={transactions} loading={isLoading}
        page={meta?.page} totalPages={meta?.total_pages} onPageChange={setPage}
        searchValue={search} onSearchChange={(v) => { setSearch(v); setPage(1); }}
        searchPlaceholder="Cari nama peminjam..."
        emptyTitle="Belum ada transaksi"
        emptyMessage="Klik 'Peminjaman Baru' untuk membuat transaksi pertama."
      />

      {/* Confirm Cancel */}
      <ConfirmDialog open={!!cancelId} onOpenChange={(o) => { if (!o) setCancelId(null); }}
        title="Batalkan Transaksi" message="Batalkan transaksi ini? Stok akan dikembalikan."
        onConfirm={() => cancelMutation.mutate(cancelId)} confirmLabel="Batalkan" variant="danger" />

      {/* Confirm Delete single */}
      <ConfirmDialog
        open={!!deleteTarget}
        onOpenChange={() => setDeleteTarget(null)}
        title="Hapus Transaksi"
        message={`Anda akan menghapus transaksi peminjaman #${deleteTarget?.id}. ${deleteTarget?.status === "Dikembalikan" ? "Transaksi dengan status Dikembalikan akan ikut menghapus data pengembalian terkait. " : ""}Data rincian barang yang dipinjam juga akan dihapus. Tindakan ini tidak dapat dibatalkan.`}
        onConfirm={() => deleteTarget && deleteMutation.mutate(deleteTarget.id)}
        confirmLabel="Hapus"
        variant="danger"
      />
    </div>
  );
}
