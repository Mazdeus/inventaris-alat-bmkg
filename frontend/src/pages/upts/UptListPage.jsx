import { useState, useMemo } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { useAuth } from "@/contexts/AuthContext";
import { uptsApi } from "@/api/upts";
import DataTable from "@/components/ui/DataTable";
import ExportButton from "@/components/ui/ExportButton";
import PageHeader from "@/components/ui/PageHeader";
import { ConfirmDialog } from "@/components/ui/ConfirmDialog";
import UptForm from "./UptForm";
import { Plus, Pencil, Trash2, Building2, MapPin, Phone, ArrowUp, ArrowDown } from "lucide-react";

/**
 * Halaman daftar UPT (Unit Pelaksana Teknis).
 */
export default function UptListPage() {
  const queryClient = useQueryClient();
  const { isAdmin } = useAuth();

  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [sortOrder, setSortOrder] = useState("asc");

  const [formOpen, setFormOpen] = useState(false);
  const [editData, setEditData] = useState(null);

  // State hapus
  const [deleteTarget, setDeleteTarget] = useState(null);

  const { data, isLoading, isError } = useQuery({
    queryKey: ["upts", page, search, sortOrder],
    queryFn: () =>
      uptsApi.getUpts({
        page,
        size: 10,
        search: search || undefined,
        order_dir: sortOrder,
      }),
    keepPreviousData: true,
  });

  const upts = data?.data?.data || [];
  const meta = data?.data?.meta;

  const displayedUpts = useMemo(() => {
    if (!upts || upts.length === 0) return [];
    const total = meta?.total ?? upts.length;
    return upts.map((item, idx) => ({
      ...item,
      __rowNumber:
        sortOrder === "desc"
          ? total - ((page - 1) * 10 + idx)
          : (page - 1) * 10 + idx + 1,
    }));
  }, [upts, page, sortOrder, meta?.total]);

  const deleteMutation = useMutation({
    mutationFn: (id) => uptsApi.deleteUpt(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["upts"] });
      toast.success("Data UPT berhasil dihapus");
      setDeleteTarget(null);
    },
    onError: (err) => {
      toast.error(err?.response?.data?.detail || "Gagal menghapus data UPT");
    },
  });

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
        <span className="text-xs font-medium text-slate-500">
          {row.__rowNumber}
        </span>
      ),
    },
    {
      key: "name",
      header: "Nama UPT",
      render: (row) => (
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-slate-100 text-slate-700">
            <Building2 className="h-4 w-4" />
          </div>
          <div>
            <span className="font-semibold text-slate-800">{row.name}</span>
          </div>
        </div>
      ),
    },
    {
      key: "address",
      header: "Alamat",
      render: (row) => (
        <div className="flex items-center gap-1.5 text-gray-600 max-w-md">
          {row.address ? (
            <>
              <MapPin className="h-3.5 w-3.5 shrink-0 text-gray-400" />
              <span className="text-xs leading-relaxed">{row.address}</span>
            </>
          ) : (
            <span className="text-gray-400 text-xs">-</span>
          )}
        </div>
      ),
    },
    {
      key: "phone",
      header: "Kontak / Telepon",
      render: (row) => (
        <div className="flex items-center gap-1.5 text-gray-600">
          {row.phone ? (
            <>
              <Phone className="h-3.5 w-3.5 shrink-0 text-gray-400" />
              <span className="font-mono text-xs">{row.phone}</span>
            </>
          ) : (
            <span className="text-gray-400 text-xs">-</span>
          )}
        </div>
      ),
    },
    ...(isAdmin
      ? [
          {
            key: "actions",
            header: "Aksi",
            render: (row) => (
              <div className="flex items-center gap-1">
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    setEditData(row);
                    setFormOpen(true);
                  }}
                  className="rounded-md p-1 text-gray-500 hover:bg-gray-100 hover:text-slate-800 transition"
                  title="Edit UPT"
                >
                  <Pencil className="h-4 w-4" />
                </button>
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    setDeleteTarget(row);
                  }}
                  className="rounded-md p-1 text-red-500 hover:bg-red-50 hover:text-red-700 transition"
                  title="Hapus UPT"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            ),
          },
        ]
      : []),
  ];

  // Fungsi mengambil seluruh data UPT yang cocok dengan pencarian untuk ekspor
  const fetchExportData = async () => {
    const res = await uptsApi.getUpts({
      page: 1,
      size: 10000,
      search: search || undefined,
      order_dir: sortOrder,
    });
    const allUpts = res?.data?.data || [];
    return allUpts.map((u, idx) => ({
      no: idx + 1,
      name: u.name || "-",
      address: u.address || "-",
      phone: u.phone || "-",
      status: u.is_active ? "Aktif" : "Nonaktif",
    }));
  };

  const exportColumns = [
    { key: "no", header: "No." },
    { key: "name", header: "Nama UPT" },
    { key: "address", header: "Alamat" },
    { key: "phone", header: "Kontak / Telepon" },
    { key: "status", header: "Status" },
  ];

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <PageHeader
          title="Daftar UPT"
          description="Master data kantor dan stasiun Unit Pelaksana Teknis (UPT) BMKG penerima pelimpahan inventaris"
        />
        <div className="flex items-center gap-2">
          <ExportButton
            fetchData={fetchExportData}
            columns={exportColumns}
            filename={`Daftar_UPT_BMKG_${new Date().toISOString().split('T')[0]}`}
            type="pdf"
            title="Daftar Unit Pelaksana Teknis (UPT) BMKG"
          />
          <ExportButton
            fetchData={fetchExportData}
            columns={exportColumns}
            filename={`Daftar_UPT_BMKG_${new Date().toISOString().split('T')[0]}`}
            type="excel"
          />
          {isAdmin && (
            <button
              type="button"
              onClick={() => {
                setEditData(null);
                setFormOpen(true);
              }}
              className="flex items-center gap-1.5 rounded-md bg-slate-800 px-3.5 py-2 text-sm font-medium text-white shadow-sm hover:bg-slate-700 transition"
            >
              <Plus className="h-4 w-4" />
              Tambah UPT
            </button>
          )}
        </div>
      </div>

      <DataTable
        columns={columns}
        data={displayedUpts}
        loading={isLoading}
        page={meta?.page}
        totalPages={meta?.total_pages}
        onPageChange={setPage}
        searchValue={search}
        onSearchChange={(v) => {
          setSearch(v);
          setPage(1);
        }}
        searchPlaceholder="Cari nama atau alamat UPT..."
        emptyTitle="Belum ada data UPT"
        emptyMessage="Data UPT akan muncul di sini setelah ditambahkan."
      />

      {/* Modal Form Tambah/Edit */}
      <UptForm
        open={formOpen}
        onClose={() => {
          setFormOpen(false);
          setEditData(null);
        }}
        editData={editData}
        onSuccess={() => {
          queryClient.invalidateQueries({ queryKey: ["upts"] });
        }}
      />

      {/* Modal Konfirmasi Hapus */}
      <ConfirmDialog
        open={!!deleteTarget}
        onOpenChange={(open) => {
          if (!open) setDeleteTarget(null);
        }}
        title="Hapus UPT"
        message={`Apakah Anda yakin ingin menghapus data UPT "${deleteTarget?.name}"? Data UPT akan dinonaktifkan.`}
        confirmLabel="Hapus"
        variant="danger"
        requirePassword
        onConfirm={() => {
          if (deleteTarget) {
            deleteMutation.mutate(deleteTarget.id);
          }
        }}
      />
    </div>
  );
}
