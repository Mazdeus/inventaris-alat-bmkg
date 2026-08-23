import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useAuth } from "@/contexts/AuthContext";
import { officersApi } from "@/api/officers";
import DataTable from "@/components/ui/DataTable";
import PageHeader from "@/components/ui/PageHeader";
import FilterBar from "@/components/ui/FilterBar";
import { ConfirmDialog } from "@/components/ui/ConfirmDialog";
import OfficerForm from "./OfficerForm";
import { Plus, Pencil, Trash2 } from "lucide-react";

/**
 * Halaman daftar petugas.
 */
export default function OfficerListPage() {
  const queryClient = useQueryClient();
  const { isAdmin } = useAuth();

  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");

  const [formOpen, setFormOpen] = useState(false);
  const [editData, setEditData] = useState(null);

  // Delete state
  const [deleteTarget, setDeleteTarget] = useState(null);

  const { data, isLoading, isError } = useQuery({
    queryKey: ["officers", page, search],
    queryFn: () =>
      officersApi.getOfficers({
        page,
        size: 10,
        search: search || undefined,
      }),
    keepPreviousData: true,
  });

  const officers = data?.data?.data || [];
  const meta = data?.data?.meta;

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: (id) => officersApi.deleteOfficer(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["officers"] });
      setDeleteTarget(null);
    },
  });

  const columns = [
    {
      key: "officer_name",
      header: "Nama Petugas",
      render: (row) => <span className="font-medium text-slate-800">{row.officer_name}</span>,
    },
    {
      key: "nip",
      header: "NIP",
      render: (row) => <span className="font-mono text-xs text-gray-600">{row.nip || "-"}</span>,
    },
    {
      key: "position",
      header: "Jabatan",
      render: (row) => <span className="text-sm text-gray-600">{row.position || "-"}</span>,
    },
    {
      key: "phone",
      header: "Telepon",
      render: (row) => (
        <span className="font-mono text-xs text-gray-600">{row.phone || "-"}</span>
      ),
    },
    {
      key: "email",
      header: "Email",
      render: (row) => <span className="text-sm text-gray-600">{row.email || "-"}</span>,
    },
    {
      key: "is_active",
      header: "Status",
      render: (row) => (
        <span
          className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium ${
            row.is_active
              ? "bg-emerald-100 text-emerald-800 border-emerald-300"
              : "bg-red-100 text-red-800 border-red-300"
          }`}
        >
          {row.is_active ? "Aktif" : "Nonaktif"}
        </span>
      ),
    },
    {
      key: "actions",
      header: "Aksi",
      render: (row) =>
        isAdmin ? (
          <div className="flex items-center gap-1">
            <button
              onClick={(e) => {
                e.stopPropagation();
                openEdit(row);
              }}
              className="rounded-md p-1 text-blue-600 hover:bg-blue-50"
              title="Ubah"
            >
              <Pencil className="h-4 w-4" />
            </button>
            <button
              onClick={(e) => {
                e.stopPropagation();
                setDeleteTarget(row);
              }}
              className="rounded-md p-1 text-red-600 hover:bg-red-50"
              title="Hapus"
            >
              <Trash2 className="h-4 w-4" />
            </button>
          </div>
        ) : null,
    },
  ];

  const filters = [];

  function openCreate() {
    setEditData(null);
    setFormOpen(true);
  }
  function openEdit(row) {
    setEditData(row);
    setFormOpen(true);
  }
  function onFormSuccess() {
    setFormOpen(false);
    setEditData(null);
    queryClient.invalidateQueries({ queryKey: ["officers"] });
  }

  return (
    <div>
      <PageHeader
        title="Petugas"
        description="Kelola data petugas yang mengeluarkan dan menerima barang"
        actions={
          isAdmin ? (
            <button
              onClick={openCreate}
              className="flex items-center gap-1 rounded-md bg-slate-800 px-3 py-2 text-sm font-medium text-white hover:bg-slate-700"
            >
              <Plus className="h-4 w-4" /> Tambah Petugas
            </button>
          ) : null
        }
      />

      {isError && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          Gagal memuat data. Pastikan backend berjalan.
        </div>
      )}

      <FilterBar filters={filters} />

      <DataTable
        columns={columns}
        data={officers}
        loading={isLoading}
        page={meta?.page}
        totalPages={meta?.total_pages}
        onPageChange={setPage}
        searchValue={search}
        onSearchChange={(v) => {
          setSearch(v);
          setPage(1);
        }}
        searchPlaceholder="Cari nama petugas..."
        emptyTitle="Belum ada petugas"
        emptyMessage="Klik 'Tambah Petugas' untuk menambahkan data petugas."
      />

      <OfficerForm
        open={formOpen}
        onClose={() => {
          setFormOpen(false);
          setEditData(null);
        }}
        editData={editData}
        onSuccess={onFormSuccess}
      />

      {/* Konfirmasi hapus */}
      <ConfirmDialog
        open={!!deleteTarget}
        onOpenChange={() => setDeleteTarget(null)}
        title="Hapus Petugas"
        message={`Anda akan menghapus petugas "${deleteTarget?.officer_name}". Petugas yang terkait transaksi tidak dapat dihapus. Tindakan ini tidak dapat dibatalkan.`}
        onConfirm={() => deleteTarget && deleteMutation.mutate(deleteTarget.id)}
        confirmLabel="Hapus"
        variant="danger"
        requirePassword
      />
    </div>
  );
}
