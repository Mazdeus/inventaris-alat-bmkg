import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { inventoryApi } from "@/api/inventory";
import DataTable from "@/components/ui/DataTable";
import PageHeader from "@/components/ui/PageHeader";
import StatusBadge from "@/components/ui/StatusBadge";
import { ConfirmDialog } from "@/components/ui/ConfirmDialog";
import PackageForm from "./PackageForm";
import { formatDate } from "@/lib/formatters";
import { PackageOpen, Plus, Pencil, Trash2, Image } from "lucide-react";

/**
 * Halaman daftar paket inventaris.
 * Fitur: search, pagination, tambah/edit/hapus (Admin), klik ke detail.
 */
export default function PackageListPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { isAdmin } = useAuth();

  // State pagination & search
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");

  // State modal
  const [formOpen, setFormOpen] = useState(false);
  const [editData, setEditData] = useState(null); // null = create, object = edit

  // State confirm delete
  const [deleteTarget, setDeleteTarget] = useState(null);

  // Fetch packages
  const { data, isLoading, isError } = useQuery({
    queryKey: ["packages", page, search],
    queryFn: () => inventoryApi.getPackages({ page, size: 10, search: search || undefined }),
    keepPreviousData: true,
  });

  const packages = data?.data?.data || [];
  const meta = data?.data?.meta;

  // Mutations
  const deleteMutation = useMutation({
    mutationFn: (id) => inventoryApi.deletePackage(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["packages"] });
      setDeleteTarget(null);
    },
  });

  /** Buka form untuk tambah */
  function openCreate() {
    setEditData(null);
    setFormOpen(true);
  }

  /** Buka form untuk edit */
  function openEdit(pkg) {
    setEditData(pkg);
    setFormOpen(true);
  }

  /** Setelah form sukses */
  function onFormSuccess() {
    setFormOpen(false);
    setEditData(null);
    queryClient.invalidateQueries({ queryKey: ["packages"] });
  }

  /** Konfirmasi hapus */
  function handleDelete() {
    if (deleteTarget) {
      deleteMutation.mutate(deleteTarget.id);
    }
  }

  // Definisi kolom tabel
  const columns = [
    {
      key: "box_number",
      header: "Nomor Box",
      render: (row) => (
        <span className="font-medium text-slate-800">{row.box_number}</span>
      ),
    },
    {
      key: "photo",
      header: "Foto",
      render: (row) =>
        row.photo ? (
          <img
            src={row.photo}
            alt={row.box_number}
            className="h-8 w-8 rounded object-cover"
            onError={(e) => { e.target.style.display = "none"; }}
          />
        ) : (
          <Image className="h-8 w-8 text-gray-300" />
        ),
    },
    {
      key: "location",
      header: "Lokasi",
      render: (row) => row.location || "-",
    },
    {
      key: "components_count",
      header: "Komponen",
      render: (row) => (
        <span className="inline-flex items-center rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-600">
          {row.components_count ?? 0}
        </span>
      ),
    },
    {
      key: "created_at",
      header: "Dibuat",
      render: (row) => formatDate(row.created_at),
    },
    {
      key: "actions",
      header: "Aksi",
      render: (row) =>
        isAdmin ? (
          <div className="flex gap-1">
            <button
              onClick={(e) => { e.stopPropagation(); openEdit(row); }}
              className="rounded-md p-1 text-blue-600 transition hover:bg-blue-50"
              title="Ubah"
            >
              <Pencil className="h-4 w-4" />
            </button>
            <button
              onClick={(e) => { e.stopPropagation(); setDeleteTarget(row); }}
              className="rounded-md p-1 text-red-600 transition hover:bg-red-50"
              title="Hapus"
            >
              <Trash2 className="h-4 w-4" />
            </button>
          </div>
        ) : null,
    },
  ];

  return (
    <div>
      <PageHeader
        title="Paket Inventaris"
        description="Kelola paket/box inventaris dan komponen di dalamnya"
        actions={
          isAdmin ? (
            <button
              onClick={openCreate}
              className="flex items-center gap-1 rounded-md bg-slate-800 px-3 py-2 text-sm font-medium text-white transition hover:bg-slate-700"
            >
              <Plus className="h-4 w-4" />
              Tambah Paket
            </button>
          ) : null
        }
      />

      {/* Error state */}
      {isError && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          Gagal memuat data. Pastikan backend berjalan dan Anda memiliki akses.
        </div>
      )}

      {/* Tabel */}
      {!isError && (
        <DataTable
          columns={columns}
          data={packages}
          loading={isLoading}
          page={meta?.page}
          totalPages={meta?.total_pages}
          onPageChange={setPage}
          searchValue={search}
          onSearchChange={setSearch}
          searchPlaceholder="Cari nomor box atau lokasi..."
          onRowClick={(row) => navigate(`/inventory/packages/${row.id}`)}
          emptyTitle="Belum ada paket"
          emptyMessage="Klik 'Tambah Paket' untuk menambahkan paket inventaris pertama."
        />
      )}

      {/* Form modal (create/edit) */}
      <PackageForm
        open={formOpen}
        onClose={() => { setFormOpen(false); setEditData(null); }}
        editData={editData}
        onSuccess={onFormSuccess}
      />

      {/* Confirm delete */}
      <ConfirmDialog
        open={!!deleteTarget}
        onOpenChange={(open) => { if (!open) setDeleteTarget(null); }}
        title="Hapus Paket"
        message={`Yakin ingin menghapus paket "${deleteTarget?.box_number}"? Komponen di dalamnya harus dipindahkan atau dihapus terlebih dahulu.`}
        onConfirm={handleDelete}
        confirmLabel="Hapus"
        variant="danger"
      />
    </div>
  );
}
