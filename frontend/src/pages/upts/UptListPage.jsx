import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { useAuth } from "@/contexts/AuthContext";
import { uptsApi } from "@/api/upts";
import DataTable from "@/components/ui/DataTable";
import PageHeader from "@/components/ui/PageHeader";
import { ConfirmDialog } from "@/components/ui/ConfirmDialog";
import UptForm from "./UptForm";
import { Plus, Pencil, Trash2, Building2, MapPin, Phone } from "lucide-react";

/**
 * Halaman daftar UPT (Unit Pelaksana Teknis).
 */
export default function UptListPage() {
  const queryClient = useQueryClient();
  const { isAdmin } = useAuth();

  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");

  const [formOpen, setFormOpen] = useState(false);
  const [editData, setEditData] = useState(null);

  // State hapus
  const [deleteTarget, setDeleteTarget] = useState(null);

  const { data, isLoading, isError } = useQuery({
    queryKey: ["upts", page, search],
    queryFn: () =>
      uptsApi.getUpts({
        page,
        size: 10,
        search: search || undefined,
      }),
    keepPreviousData: true,
  });

  const upts = data?.data?.data || [];
  const meta = data?.data?.meta;

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

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <PageHeader
          title="Daftar UPT"
          description="Master data kantor dan stasiun Unit Pelaksana Teknis (UPT) BMKG penerima pelimpahan inventaris"
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

      <DataTable
        columns={columns}
        data={upts}
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
