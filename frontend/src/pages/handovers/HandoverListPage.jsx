import { useState, useRef, useMemo } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { handoversApi } from "@/api/handovers";
import { STATUS_LABELS } from "@/lib/constants";
import DataTable from "@/components/ui/DataTable";
import ExportButton from "@/components/ui/ExportButton";
import PageHeader from "@/components/ui/PageHeader";
import FilterBar from "@/components/ui/FilterBar";
import { ConfirmDialog } from "@/components/ui/ConfirmDialog";
import { Plus, FileDown, FileUp, Eye, Trash2, Pencil, ArrowUp, ArrowDown } from "lucide-react";
import { formatDate } from "@/lib/formatters";
import { toast } from "sonner";
import DatePresetFilter from "@/components/ui/DatePresetFilter";

const STATUS_OPTIONS = [
  { value: "Draft", label: "Draft" },
  { value: "Transferred", label: "Dilimpahkan" },
  { value: "Cancelled", label: "Dibatalkan" },
];

const canUploadDoc = (status) => status === "Draft";

export default function HandoverListPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { isAdmin } = useAuth();
  const uploadRefs = useRef({});
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [filterStatus, setFilterStatus] = useState(null);
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [sortOrder, setSortOrder] = useState("asc");
  const [deleteTarget, setDeleteTarget] = useState(null);

  const { data, isLoading, isError } = useQuery({
    queryKey: ["handovers", page, search, filterStatus, startDate, endDate, sortOrder],
    queryFn: () =>
      handoversApi.getHandovers({
        page,
        size: 10,
        search: search || undefined,
        status: filterStatus || undefined,
        start_date: startDate || undefined,
        end_date: endDate || undefined,
        order_dir: sortOrder,
      }),
    keepPreviousData: true,
  });

  const handovers = data?.data?.data || [];
  const meta = data?.data?.meta;

  const displayedHandovers = useMemo(() => {
    if (!handovers || handovers.length === 0) return [];
    const total = meta?.total ?? handovers.length;
    return handovers.map((item, idx) => ({
      ...item,
      __rowNumber: sortOrder === "desc"
        ? total - ((page - 1) * 10 + idx)
        : (page - 1) * 10 + idx + 1,
    }));
  }, [handovers, page, sortOrder, meta?.total]);

  const deleteMutation = useMutation({
    mutationFn: (id) => handoversApi.deleteHandover(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["handovers"] });
      setDeleteTarget(null);
      toast.success("Pelimpahan berhasil dihapus");
    },
    onError: (err) => {
      toast.error(err?.response?.data?.detail || "Gagal menghapus pelimpahan");
    },
  });

  function handleDownloadDoc(id, e) {
    e.stopPropagation();
    handoversApi.downloadDocument(id).then((res) => {
      const blob = new Blob([res.data], { type: "application/pdf" });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `BAST_Pelimpahan_${id}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    }).catch(() => toast.error("Gagal mengunduh dokumen"));
  }

  function handleUploadClick(id) {
    uploadRefs.current[id]?.click();
  }

  function handleUploadFile(id, file) {
    if (!file) return;
    handoversApi.uploadDocument(id, file).then(() => {
      queryClient.invalidateQueries({ queryKey: ["handovers"] });
      toast.success("Dokumen berhasil diupload");
    }).catch((err) => toast.error(err?.response?.data?.detail || "Gagal upload dokumen"));
  }

  const columns = [
    {
      key: "no",
      header: (
        <button
          type="button"
          onClick={() => {
            setSortOrder((prev) => (prev === "asc" ? "desc" : "asc"));
            setPage(1);
          }}
          className="flex items-center gap-1 hover:text-slate-900 transition-colors cursor-pointer group"
          title={`Urutkan: ${sortOrder === "asc" ? "Menaik (Ascending) - Klik untuk Menurun" : "Menurun (Descending) - Klik untuk Menaik"}`}
        >
          <span>No.</span>
          {sortOrder === "asc" ? (
            <ArrowUp className="h-3 w-3 text-slate-500 group-hover:text-slate-900 transition-colors" />
          ) : (
            <ArrowDown className="h-3 w-3 text-slate-500 group-hover:text-slate-900 transition-colors" />
          )}
        </button>
      ),
      width: "w-12",
      render: (row) => (
        <span className="text-xs font-medium text-slate-500">{row.__rowNumber}</span>
      ),
    },
    {
      key: "transaction_number",
      header: "No. Transaksi",
      render: (row) => (
        <span className="font-mono text-xs font-medium text-slate-700">
          {row.transaction_number || `#${row.id}`}
        </span>
      ),
    },
    {
      key: "upt_receiver",
      header: "UPT Penerima",
      render: (row) => (
        <div>
          <span className="font-medium text-slate-800">{row.upt_receiver}</span>
          {row.recipient_name && (
            <div className="text-xs text-gray-500">Penerima: {row.recipient_name}</div>
          )}
        </div>
      ),
    },
    {
      key: "handover_date",
      header: "Tanggal",
      render: (row) => row.handover_date || "-",
    },
    {
      key: "status",
      header: "Status",
      render: (row) => (
        <span className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${
          row.status === "Transferred" ? "bg-emerald-100 text-emerald-800" :
          row.status === "Draft" ? "bg-yellow-100 text-yellow-800" :
          row.status === "Cancelled" ? "bg-red-100 text-red-800" :
          "bg-gray-100 text-gray-600"
        }`}>{STATUS_LABELS[row.status] || row.status}</span>
      ),
    },
    {
      key: "items_count",
      header: "Barang",
      render: (row) => {
        const items = row.items || [];
        const names = [...new Set(items.map((it) => it.component_name).filter(Boolean))].join(", ");
        return (
          <div>
            <span className="text-sm font-medium text-slate-800">{row.items_count} barang</span>
            {names && (
              <div className="text-xs text-gray-500 truncate max-w-[160px]" title={names}>
                {names}
              </div>
            )}
          </div>
        );
      },
    },
    {
      key: "created_at",
      header: "Dibuat",
      render: (row) => formatDate(row.created_at),
    },
    {
      key: "actions",
      header: "Aksi",
      render: (row) => (
        <div className="flex gap-1">
          <button onClick={(e) => { e.stopPropagation(); navigate(`/handovers/${row.id}`); }}
            className="rounded-md p-1 text-gray-500 hover:bg-gray-100" title="Detail">
            <Eye className="h-4 w-4" />
          </button>
          {/* Download Document — selalu tersedia */}
          <button onClick={(e) => handleDownloadDoc(row.id, e)}
            className="rounded-md p-1 text-blue-600 hover:bg-blue-50" title="Unduh Dokumen">
            <FileDown className="h-4 w-4" />
          </button>
          {/* Upload Document — hanya saat status Draft */}
          {canUploadDoc(row.status) && (
            <button onClick={(e) => { e.stopPropagation(); handleUploadClick(row.id); }}
              className="rounded-md p-1 text-purple-600 hover:bg-purple-50" title="Unggah Dokumen Tertandatangan">
              <FileUp className="h-4 w-4" />
              <input type="file" ref={(el) => { uploadRefs.current[row.id] = el; }}
                accept=".pdf,.png,.jpg,.jpeg"
                onChange={(e) => handleUploadFile(row.id, e.target.files?.[0], e)}
                className="hidden" />
            </button>
          )}
          {/* Edit — hanya status Draft */}
          {isAdmin && row.status === "Draft" && (
            <button onClick={(e) => { e.stopPropagation(); navigate(`/handovers/${row.id}/edit`); }}
              className="rounded-md p-1 text-blue-600 hover:bg-blue-50" title="Ubah Pelimpahan">
              <Pencil className="h-4 w-4" />
            </button>
          )}
          {/* Hapus — hanya status Draft */}
          {isAdmin && row.status === "Draft" && (
            <button onClick={(e) => { e.stopPropagation(); setDeleteTarget(row); }}
              className="rounded-md p-1 text-red-600 hover:bg-red-50" title="Hapus Pelimpahan">
              <Trash2 className="h-4 w-4" />
            </button>
          )}
        </div>
      ),
    },
  ];

  const filters = [
    {
      label: "Status",
      key: "status",
      value: filterStatus,
      onChange: (v) => { setFilterStatus(v || null); setPage(1); },
      options: STATUS_OPTIONS,
    },
  ];

  // Fungsi mengambil seluruh data yang cocok dengan filter untuk ekspor (lintas halaman)
  const fetchExportData = async () => {
    const res = await handoversApi.getHandovers({
      page: 1,
      size: 10000,
      search: search || undefined,
      status: filterStatus || undefined,
      start_date: startDate || undefined,
      end_date: endDate || undefined,
      order_dir: sortOrder,
    });
    const allHandovers = res?.data?.data || [];
    const rows = [];
    const spanKeys = ["no", "transaction_number", "upt_receiver", "recipient_name", "recipient_nip", "officer_name", "handover_date", "status"];

    allHandovers.forEach((h, idx) => {
      const items = h.items || [];
      const compGroups = {};
      items.forEach((it) => {
        const name = it.component_name || "-";
        if (!compGroups[name]) compGroups[name] = [];
        if (it.serial_number) compGroups[name].push(it.serial_number);
      });
      const compNames = Object.keys(compGroups);
      const txNum = h.transaction_number || `#${h.id}`;
      const uptReceiver = h.upt_receiver || "-";
      const recipientName = h.recipient_name || "-";
      const recipientNip = h.recipient_nip || "-";
      const officer = h.officer_name || "-";
      const handoverDate = formatDate(h.handover_date);
      const statusLabel = STATUS_LABELS[h.status] || h.status || "-";

      if (compNames.length <= 1) {
        const name = compNames[0] || "-";
        const sns = compNames.length > 0 ? compGroups[name] : [];
        const count = compNames.length > 0 ? (compGroups[name].length || 1) : (h.items_count || items.length);
        rows.push({
          no: idx + 1,
          transaction_number: txNum,
          upt_receiver: uptReceiver,
          recipient_name: recipientName,
          recipient_nip: recipientNip,
          officer_name: officer,
          handover_date: handoverDate,
          unit_name: name,
          items_count: count,
          serial_number: sns.length > 0 ? sns.join(", ") : "-",
          status: statusLabel,
        });
      } else {
        compNames.forEach((name, cIdx) => {
          const sns = compGroups[name];
          const count = sns.length || 1;
          const snStr = sns.length > 0 ? sns.join(", ") : "-";

          if (cIdx === 0) {
            rows.push({
              no: idx + 1,
              transaction_number: txNum,
              upt_receiver: uptReceiver,
              recipient_name: recipientName,
              recipient_nip: recipientNip,
              officer_name: officer,
              handover_date: handoverDate,
              unit_name: name,
              items_count: count,
              serial_number: snStr,
              status: statusLabel,
              _rowSpan: compNames.length,
              _spanKeys: spanKeys,
            });
          } else {
            rows.push({
              no: "",
              transaction_number: "",
              upt_receiver: "",
              recipient_name: "",
              recipient_nip: "",
              officer_name: "",
              handover_date: "",
              unit_name: name,
              items_count: count,
              serial_number: snStr,
              status: "",
              _isSubRow: true,
              _spanKeys: spanKeys,
            });
          }
        });
      }
    });

    return rows;
  };

  const exportColumns = [
    { key: "no", header: "No." },
    { key: "transaction_number", header: "No. Transaksi" },
    { key: "upt_receiver", header: "UPT Penerima" },
    { key: "recipient_name", header: "Nama Penerima" },
    { key: "recipient_nip", header: "NIP Penerima" },
    { key: "officer_name", header: "Petugas Penyerah" },
    { key: "handover_date", header: "Tgl Pelimpahan" },
    { key: "unit_name", header: "Nama Barang" },
    { key: "items_count", header: "Jumlah" },
    { key: "serial_number", header: "Serial Number" },
    { key: "status", header: "Status" },
  ];

  return (
    <div>
      <PageHeader
        title="Pelimpahan"
        description="Kelola pelimpahan barang inventaris ke UPT"
        actions={
          isAdmin ? (
            <button onClick={() => navigate("/handovers/new")}
              className="flex items-center gap-1 rounded-md bg-slate-800 px-3 py-2 text-sm font-medium text-white hover:bg-slate-700">
              <Plus className="h-4 w-4" /> Pelimpahan Baru
            </button>
          ) : null
        }
      />

      {isError && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          Gagal memuat data.
        </div>
      )}

      <div className="mb-4 flex flex-wrap items-center gap-3">
        <FilterBar filters={filters} />
        <DatePresetFilter
          startDate={startDate}
          endDate={endDate}
          onChange={(s, e) => {
            setStartDate(s);
            setEndDate(e);
            setPage(1);
          }}
        />
        <div className="ml-auto flex items-center gap-2">
          <ExportButton fetchData={fetchExportData} columns={exportColumns}
            filename={`Laporan_Pelimpahan_${startDate || 'all'}_${endDate || 'all'}`}
            type="pdf" title="Laporan Pelimpahan UPT BMKG" />
          <ExportButton fetchData={fetchExportData} columns={exportColumns}
            filename={`Laporan_Pelimpahan_${startDate || 'all'}_${endDate || 'all'}`}
            type="excel" />
        </div>
      </div>

      <DataTable
        columns={columns}
        data={displayedHandovers}
        loading={isLoading}
        page={meta?.page}
        totalPages={meta?.total_pages}
        onPageChange={setPage}
        searchValue={search}
        onSearchChange={(v) => { setSearch(v); setPage(1); }}
        searchPlaceholder="Cari No. Transaksi atau UPT penerima..."
        onRowClick={(row) => navigate(`/handovers/${row.id}`)}
        emptyTitle="Belum ada pelimpahan"
        emptyMessage="Klik 'Pelimpahan Baru' untuk melimpahkan barang ke UPT."
      />

      <ConfirmDialog
        open={!!deleteTarget}
        onOpenChange={() => setDeleteTarget(null)}
        title="Hapus Pelimpahan"
        message={`Anda akan menghapus pelimpahan #${deleteTarget?.id} ke UPT "${deleteTarget?.upt_receiver}".`}
        onConfirm={() => deleteTarget && deleteMutation.mutate(deleteTarget.id)}
        confirmLabel="Hapus"
        variant="danger"
        requirePassword
      />
    </div>
  );
}
