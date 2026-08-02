import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useAuth } from "@/contexts/AuthContext";
import { borrowersApi } from "@/api/borrowers";
import DataTable from "@/components/ui/DataTable";
import PageHeader from "@/components/ui/PageHeader";
import FilterBar from "@/components/ui/FilterBar";
import StatusBadge from "@/components/ui/StatusBadge";
import { ConfirmDialog } from "@/components/ui/ConfirmDialog";
import BorrowerForm from "./BorrowerForm";
import { truncateText } from "@/lib/formatters";
import { Plus, Pencil, Trash2, Loader2 } from "lucide-react";

/**
 * Halaman daftar peminjam.
 */
export default function BorrowerListPage() {
  const queryClient = useQueryClient();
  const { isAdmin } = useAuth();

  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [filterType, setFilterType] = useState(null);

  const [formOpen, setFormOpen] = useState(false);
  const [editData, setEditData] = useState(null);
  const [selectedIds, setSelectedIds] = useState([]);
  const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false);

  const { data, isLoading, isError } = useQuery({
    queryKey: ["borrowers", page, search, filterType],
    queryFn: () =>
      borrowersApi.getBorrowers({
        page, size: 10,
        search: search || undefined,
        borrower_type: filterType || undefined,
      }),
    keepPreviousData: true,
  });

  const borrowers = data?.data?.data || [];
  const meta = data?.data?.meta;

  const deleteMutation = useMutation({
    mutationFn: (data) => borrowersApi.bulkDelete(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["borrowers"] });
      setSelectedIds([]);
    },
  });

  function toggleSelectAll() {
    if (selectedIds.length === borrowers.length) {
      setSelectedIds([]);
    } else {
      setSelectedIds(borrowers.map((b) => b.id));
    }
  }
  function toggleSelect(id) {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((i) => i !== id) : [...prev, id]
    );
  }
  function handleBulkDelete() {
    setDeleteConfirmOpen(true);
  }
  function confirmBulkDelete() {
    deleteMutation.mutate({ ids: selectedIds });
    setDeleteConfirmOpen(false);
  }

  const columns = [
    {
      key: "checkbox",
      header: (
        <input
          type="checkbox"
          checked={borrowers.length > 0 && selectedIds.length === borrowers.length}
          onChange={toggleSelectAll}
          className="h-4 w-4 rounded border-gray-300 text-slate-800 focus:ring-slate-400"
        />
      ),
      render: (row) => (
        <input
          type="checkbox"
          checked={selectedIds.includes(row.id)}
          onChange={() => toggleSelect(row.id)}
          className="h-4 w-4 rounded border-gray-300 text-slate-800 focus:ring-slate-400"
        />
      ),
    },
    {
      key: "borrower_name",
      header: "Nama Peminjam",
      render: (row) => <span className="font-medium text-slate-800">{row.borrower_name}</span>,
    },
    {
      key: "borrower_type",
      header: "Tipe",
      render: (row) => <StatusBadge type="borrower" value={row.borrower_type} />,
    },
    {
      key: "institution",
      header: "Instansi",
      render: (row) => row.institution || "-",
    },
    {
      key: "nip",
      header: "NIP/NIK",
      render: (row) => (
        <span className="font-mono text-xs text-gray-600">{row.nip || "-"}</span>
      ),
    },
    {
      key: "email",
      header: "Email",
      render: (row) => <span className="text-sm text-gray-600">{row.email || "-"}</span>,
    },
    {
      key: "phone",
      header: "Telepon",
      render: (row) => (
        <span className="font-mono text-xs text-gray-600">{row.phone || "-"}</span>
      ),
    },
    {
      key: "address",
      header: "Alamat",
      render: (row) => (
        <span className="text-sm text-gray-600">{truncateText(row.address, 50) || "-"}</span>
      ),
    },
    {
      key: "actions",
      header: "Aksi",
      render: (row) =>
        isAdmin ? (
          <button
            onClick={(e) => { e.stopPropagation(); openEdit(row); }}
            className="rounded-md p-1 text-blue-600 hover:bg-blue-50" title="Ubah"
          >
            <Pencil className="h-4 w-4" />
          </button>
        ) : null,
    },
  ];

  const filters = [
    {
      label: "Tipe", key: "type", value: filterType,
      onChange: (v) => { setFilterType(v || null); setPage(1); },
      options: [
        { value: "Internal", label: "Internal" },
        { value: "External", label: "Eksternal" },
      ],
    },
  ];

  function openCreate() { setEditData(null); setFormOpen(true); }
  function openEdit(row) { setEditData(row); setFormOpen(true); }
  function onFormSuccess() { setFormOpen(false); setEditData(null);
    queryClient.invalidateQueries({ queryKey: ["borrowers"] });
  }

  return (
    <div>
      <PageHeader
        title="Peminjam"
        description="Kelola data peminjam internal dan eksternal"
        actions={
          isAdmin ? (
            <div className="flex items-center gap-2">
              {selectedIds.length > 0 && (
                <button
                  onClick={handleBulkDelete}
                  disabled={deleteMutation.isPending}
                  className="flex items-center gap-1 rounded-md border border-red-300 bg-white px-3 py-2 text-sm font-medium text-red-600 hover:bg-red-50 disabled:opacity-60"
                >
                  {deleteMutation.isPending ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Trash2 className="h-4 w-4" />
                  )}
                  Hapus Terpilih ({selectedIds.length})
                </button>
              )}
              <button onClick={openCreate} className="flex items-center gap-1 rounded-md bg-slate-800 px-3 py-2 text-sm font-medium text-white hover:bg-slate-700">
                <Plus className="h-4 w-4" /> Tambah Peminjam
              </button>
            </div>
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
        columns={columns} data={borrowers} loading={isLoading}
        page={meta?.page} totalPages={meta?.total_pages} onPageChange={setPage}
        searchValue={search} onSearchChange={(v) => { setSearch(v); setPage(1); }}
        searchPlaceholder="Cari nama peminjam..."
        emptyTitle="Belum ada peminjam"
        emptyMessage="Klik 'Tambah Peminjam' untuk menambahkan data peminjam."
      />

      <BorrowerForm open={formOpen} onClose={() => { setFormOpen(false); setEditData(null); }}
        editData={editData} onSuccess={onFormSuccess} />

      {/* Bulk delete confirmation dialog */}
      <ConfirmDialog
        open={deleteConfirmOpen}
        onClose={() => setDeleteConfirmOpen(false)}
        onConfirm={confirmBulkDelete}
        title="Hapus Peminjam Terpilih"
        message={`Yakin ingin menghapus ${selectedIds.length} peminjam yang dipilih? Tindakan ini tidak dapat dibatalkan. Peminjam dengan riwayat transaksi akan diblokir.`}
        confirmLabel={deleteMutation.isPending ? "Menghapus..." : "Hapus"}
        variant="danger"
      />
    </div>
  );
}
