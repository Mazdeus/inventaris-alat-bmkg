import { useState, useRef } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { handoversApi } from "@/api/handovers";
import DataTable from "@/components/ui/DataTable";
import PageHeader from "@/components/ui/PageHeader";
import FilterBar from "@/components/ui/FilterBar";
import { Plus, FileDown, FileUp, Eye } from "lucide-react";
import { formatDate } from "@/lib/formatters";
import { toast } from "sonner";

const STATUS_OPTIONS = [
  { value: "Draft", label: "Draft" },
  { value: "Dilimpahkan", label: "Dilimpahkan" },
  { value: "Dibatalkan", label: "Dibatalkan" },
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

  const { data, isLoading, isError } = useQuery({
    queryKey: ["handovers", page, search, filterStatus],
    queryFn: () =>
      handoversApi.getHandovers({
        page,
        size: 10,
        search: search || undefined,
        status: filterStatus || undefined,
      }),
    keepPreviousData: true,
  });

  const handovers = data?.data?.data || [];
  const meta = data?.data?.meta;

  function handleDownloadDoc(id, e) {
    e.stopPropagation();
    handoversApi.downloadDocument(id).then((res) => {
      const blob = new Blob([res.data], { type: "text/plain" });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `pelimpahan_${id}.txt`;
      a.click();
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
      key: "id",
      header: "ID",
      width: "w-14",
      render: (row) => <span className="font-mono text-xs text-slate-500">#{row.id}</span>,
    },
    {
      key: "upt_receiver",
      header: "UPT Penerima",
      render: (row) => <span className="font-medium text-slate-800">{row.upt_receiver}</span>,
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
          row.status === "Dilimpahkan" ? "bg-emerald-100 text-emerald-800" :
          row.status === "Draft" ? "bg-yellow-100 text-yellow-800" :
          row.status === "Dibatalkan" ? "bg-red-100 text-red-800" :
          "bg-gray-100 text-gray-600"
        }`}>{row.status}</span>
      ),
    },
    {
      key: "items_count",
      header: "Barang",
      render: (row) => <span className="text-sm">{row.items_count}</span>,
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

      <FilterBar filters={filters} />

      <DataTable
        columns={columns}
        data={handovers}
        loading={isLoading}
        page={meta?.page}
        totalPages={meta?.total_pages}
        onPageChange={setPage}
        searchValue={search}
        onSearchChange={(v) => { setSearch(v); setPage(1); }}
        searchPlaceholder="Cari UPT penerima..."
        onRowClick={(row) => navigate(`/handovers/${row.id}`)}
        emptyTitle="Belum ada pelimpahan"
        emptyMessage="Klik 'Pelimpahan Baru' untuk melimpahkan barang ke UPT."
      />
    </div>
  );
}
