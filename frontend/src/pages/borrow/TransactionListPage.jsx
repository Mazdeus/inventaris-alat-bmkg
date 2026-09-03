import { useState, useRef, useMemo } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { borrowApi } from "@/api/borrow";
import { sendTransactionReminder } from "@/api/reminders";
import DataTable from "@/components/ui/DataTable";
import ExportButton from "@/components/ui/ExportButton";
import PageHeader from "@/components/ui/PageHeader";
import FilterBar from "@/components/ui/FilterBar";
import StatusBadge from "@/components/ui/StatusBadge";
import { ConfirmDialog } from "@/components/ui/ConfirmDialog";
import EmailControlModal from "@/components/EmailControlModal";
import { formatDate } from "@/lib/formatters";
import { toast } from "sonner";
import { Plus, Eye, Ban, FileDown, FileUp, Trash2, Pencil, Mail, Send } from "lucide-react";

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

  // Email Control Modal & State
  const [emailModalOpen, setEmailModalOpen] = useState(false);
  const [emailTargetTx, setEmailTargetTx] = useState(null);

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

  const sendEmailMutation = useMutation({
    mutationFn: ({ txId, type }) => sendTransactionReminder(txId, type),
    onSuccess: (res) => {
      toast.success(res.message || "Email alert berhasil dikirim ke Admin!");
      setEmailTargetTx(null);
    },
    onError: (err) => {
      toast.error(err?.response?.data?.detail || "Gagal mengirim email alert.");
    },
  });

  // Helper: hitung badge tenggat waktu (hanya untuk status Dipinjam)
  const getDueBadge = (expectedReturnDate, status) => {
    if (status !== "Borrowed" && status !== "Dipinjam") {
      return null;
    }
    if (!expectedReturnDate) return null;

    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const dueDate = new Date(expectedReturnDate);
    dueDate.setHours(0, 0, 0, 0);

    const diffTime = dueDate.getTime() - today.getTime();
    const diffDays = Math.round(diffTime / (1000 * 60 * 60 * 24));

    if (diffDays === 2) {
      return (
        <span className="inline-flex items-center rounded-full bg-amber-100 px-2 py-0.5 text-[10px] font-bold text-amber-800 border border-amber-300">
          🟡 H-2
        </span>
      );
    }
    if (diffDays === 1) {
      return (
        <span className="inline-flex items-center rounded-full bg-amber-100 px-2 py-0.5 text-[10px] font-bold text-amber-800 border border-amber-300">
          🟡 Besok
        </span>
      );
    }
    if (diffDays === 0) {
      return (
        <span className="inline-flex items-center rounded-full bg-blue-100 px-2 py-0.5 text-[10px] font-bold text-blue-800 border border-blue-300">
          🔵 Hari Ini
        </span>
      );
    }
    if (diffDays < 0) {
      return (
        <span className="inline-flex items-center rounded-full bg-red-100 px-2 py-0.5 text-[10px] font-bold text-red-800 border border-red-300 animate-pulse">
          🔴 Terlambat {Math.abs(diffDays)}hr
        </span>
      );
    }
    return null;
  };


  // Helper: upload dokumen hanya saat status Menunggu
  const canUploadDoc = (status) => status === "Pending";

  // Document download
  function handleDownloadDoc(id) {
    borrowApi.downloadDocument(id).then((res) => {
      const blob = new Blob([res.data], { type: "application/pdf" });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `peminjaman_${id}.pdf`;
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
  const isDeletable = (status) => status === "Pending";
  // Check if transaction is editable
  const isEditable = (status) => status === "Pending" || status === "Borrowed";

  const columns = [
    { key: "daily_sequence", header: "No.", render: (row) => <span className="text-xs text-gray-500">{row.daily_sequence ?? "-"}</span> },
    { key: "transaction_number", header: "No. Transaksi", render: (row) => <span className="font-mono text-xs font-medium text-slate-700">{row.transaction_number || `#${row.id}`}</span> },
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
    {
      key: "expected_return_date",
      header: "Tgl Kembali",
      render: (row) => (
        <div className="flex flex-col gap-1 items-start">
          <span className="text-xs">{formatDate(row.expected_return_date)}</span>
          {getDueBadge(row.expected_return_date, row.status)}
        </div>
      ),
    },
    { key: "total_items", header: "Jumlah Barang", render: (row) => <span className="font-medium">{row.total_items ?? 0}</span> },
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
          {/* Admin: Kirim Alert Email ke Admin (Hanya jika status Dipinjam) */}
          {isAdmin && (row.status === "Borrowed" || row.status === "Dipinjam") && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                setEmailTargetTx(row);
              }}
              className="rounded-md p-1 text-indigo-600 hover:bg-indigo-50"
              title="Kirim Email Alert ke Admin"
            >
              <Mail className="h-4 w-4" />
            </button>
          )}

          {/* Admin: Cancel (Dipinjam) */}
          {isAdmin && row.status === "Borrowed" && (
            <button onClick={(e) => { e.stopPropagation(); setCancelId(row.id); }}
              className="rounded-md p-1 text-orange-600 hover:bg-orange-50" title="Batalkan">
              <Ban className="h-4 w-4" />
            </button>
          )}
          {/* Admin: Edit (Menunggu, Dipinjam) */}

          {isAdmin && isEditable(row.status) && (
            <button onClick={(e) => { e.stopPropagation(); navigate(`/borrow/transactions/${row.id}/edit`); }}
              className="rounded-md p-1 text-blue-600 hover:bg-blue-50" title="Ubah">
              <Pencil className="h-4 w-4" />
            </button>
          )}
          {/* Admin: Hapus (Menunggu) */}
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

  // Data export: satu baris per komponen/unit dalam transaksi.
  const exportRows = useMemo(() => {
    const rows = [];
    (transactions || []).forEach((tx) => {
      const details = tx.details || [];
      const borrower = `${tx.borrower?.borrower_name || "-"} (${tx.borrower?.borrower_type || "-"})`;
      const officer = tx.officer_name || "-";
      const borrowDate = formatDate(tx.borrow_date);
      const returnDate = formatDate(tx.expected_return_date);
      if (details.length === 0) {
        rows.push({
          id: `#${tx.id}`,
          borrower_name: borrower,
          officer_name: officer,
          borrow_date: borrowDate,
          return_date: returnDate,
          item_name: "-",
          brand: "-",
          model: "-",
          quantity: tx.total_items ?? 0,
          serial_number: "-",
          status: tx.status,
        });
      } else {
        details.forEach((d) => {
          const sns = (d.selected_items || []).map((si) => si.serial_number || "-");
          rows.push({
            id: `#${tx.id}`,
            borrower_name: borrower,
            officer_name: officer,
            borrow_date: borrowDate,
            return_date: returnDate,
            item_name: d.component?.item_name || "-",
            brand: d.component?.brand || "-",
            model: d.component?.model || "-",
            quantity: d.quantity ?? 0,
            serial_number: sns.length ? sns.join("\n") : "-",
            status: tx.status,
          });
        });
      }
    });
    return rows;
  }, [transactions]);

  const exportColumns = [
    { key: "id", header: "ID" },
    { key: "borrower_name", header: "Peminjam" },
    { key: "officer_name", header: "Petugas" },
    { key: "borrow_date", header: "Tgl Pinjam" },
    { key: "return_date", header: "Tgl Kembali" },
    { key: "item_name", header: "Nama Barang" },
    { key: "brand", header: "Merek" },
    { key: "model", header: "Model" },
    { key: "quantity", header: "Jumlah" },
    { key: "serial_number", header: "Serial Number" },
    { key: "status", header: "Status" },
  ];

  const filters = [
    {
      label: "Status", key: "status", value: filterStatus,
      onChange: (v) => { setFilterStatus(v || null); setPage(1); },
      options: [
        { value: "Pending", label: "Menunggu" },
        { value: "Borrowed", label: "Dipinjam" },
        { value: "Returned", label: "Dikembalikan" },
        { value: "Cancelled", label: "Dibatalkan" },
      ],
    },
  ];

  return (
    <div>
      <PageHeader
        title="Peminjaman"
        description="Transaksi peminjaman inventaris"
        actions={
          <div className="flex items-center gap-2">
            {isAdmin && (
              <button
                onClick={() => setEmailModalOpen(true)}
                className="flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50 shadow-sm transition-colors"
                title="Pengaturan notifikasi email dan uji coba pengiriman"
              >
                <Mail className="h-3.5 w-3.5 text-blue-600" /> Notifikasi Email
              </button>
            )}
            {isAuthenticated && (
              <button onClick={() => navigate("/borrow/transactions/new")}
                className="flex items-center gap-1.5 rounded-lg bg-slate-900 px-3 py-2 text-xs font-semibold text-white hover:bg-slate-800 shadow-sm transition-colors">
                <Plus className="h-3.5 w-3.5" /> Peminjaman Baru
              </button>
            )}
          </div>
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
          <ExportButton data={exportRows} columns={exportColumns}
            filename={`Laporan_Peminjaman_${startDate || 'all'}_${endDate || 'all'}`}
            type="pdf" title="Laporan Peminjaman BMKG" />
          <ExportButton data={exportRows} columns={exportColumns}
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
        message={`Anda akan menghapus transaksi peminjaman #${deleteTarget?.id}. Data rincian barang yang dipinjam juga akan dihapus. Tindakan ini tidak dapat dibatalkan.`}
        onConfirm={() => deleteTarget && deleteMutation.mutate(deleteTarget.id)}
        confirmLabel="Hapus"
        variant="danger"
        requirePassword
      />

      {/* Confirm Send Email Alert */}
      <ConfirmDialog
        open={!!emailTargetTx}
        onOpenChange={() => setEmailTargetTx(null)}
        title="Kirim Email Alert ke Admin"
        message={`Kirim laporan email alert sekarang untuk transaksi peminjaman ${emailTargetTx?.transaction_number || '#' + emailTargetTx?.id} (${emailTargetTx?.borrower?.borrower_name || 'Peminjam'}) ke seluruh akun Admin aktif?`}
        onConfirm={() => emailTargetTx && sendEmailMutation.mutate({ txId: emailTargetTx.id, type: "manual" })}
        confirmLabel={sendEmailMutation.isPending ? "Mengirim..." : "Kirim Email Alert"}
        variant="primary"
      />

      {/* Modal Kontrol Email & Test SMTP */}
      <EmailControlModal
        open={emailModalOpen}
        onClose={() => setEmailModalOpen(false)}
      />
    </div>
  );
}

