import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { usersApi } from "@/api/users";
import DataTable from "@/components/ui/DataTable";
import PageHeader from "@/components/ui/PageHeader";
import { ConfirmDialog } from "@/components/ui/ConfirmDialog";
import UserForm from "./UserForm";
import { formatDate } from "@/lib/formatters";
import { Plus, Pencil, Trash2 } from "lucide-react";

export default function UserListPage() {
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [formOpen, setFormOpen] = useState(false);
  const [editData, setEditData] = useState(null);
  const [deleteTarget, setDeleteTarget] = useState(null);

  const { data, isLoading, isError } = useQuery({
    queryKey: ["users", page, search],
    queryFn: () => usersApi.getUsers({ page, size: 10, search: search || undefined }),
    keepPreviousData: true,
  });

  const users = data?.data?.data || [];
  const meta = data?.data?.meta;

  const deleteMutation = useMutation({
    mutationFn: (id) => usersApi.deleteUser(id),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ["users"] }); setDeleteTarget(null); },
    onError: (err) => {
      alert(err.response?.data?.message || "Gagal menghapus pengguna. Mungkin pengguna masih punya data terkait.");
      setDeleteTarget(null);
    },
  });

  const columns = [
    { key: "username", header: "Nama Pengguna", render: (r) => <span className="font-mono text-sm font-medium">{r.username}</span> },
    { key: "full_name", header: "Nama Lengkap", render: (r) => r.full_name || "-" },
    { key: "email", header: "Email", render: (r) => r.email || "-" },
    { key: "phone", header: "No HP", render: (r) => r.phone || "-" },
    { key: "is_active", header: "Status", render: (r) => r.is_active !== false
      ? <span className="inline-flex rounded-full bg-emerald-100 px-2 py-0.5 text-xs font-medium text-emerald-800">Aktif</span>
      : <span className="inline-flex rounded-full bg-red-100 px-2 py-0.5 text-xs font-medium text-red-800">Nonaktif</span> },
    { key: "created_at", header: "Dibuat", render: (r) => formatDate(r.created_at) },
    { key: "actions", header: "Aksi", render: (r) => (
      <div className="flex gap-1">
        <button onClick={(e) => { e.stopPropagation(); openEdit(r); }} className="rounded-md p-1 text-blue-600 hover:bg-blue-50"><Pencil className="h-4 w-4" /></button>
        <button onClick={(e) => { e.stopPropagation(); setDeleteTarget(r); }} className="rounded-md p-1 text-red-600 hover:bg-red-50"><Trash2 className="h-4 w-4" /></button>
      </div>
    )},
  ];

  function openCreate() { setEditData(null); setFormOpen(true); }
  function openEdit(row) { setEditData(row); setFormOpen(true); }
  function onFormSuccess() { setFormOpen(false); setEditData(null); queryClient.invalidateQueries({ queryKey: ["users"] }); }

  return (
    <div>
      <PageHeader title="Akun Admin" description="Kelola akun administrator sistem"
        actions={<button onClick={openCreate} className="flex items-center gap-1 rounded-md bg-slate-800 px-3 py-2 text-sm font-medium text-white hover:bg-slate-700"><Plus className="h-4 w-4" /> Tambah Admin</button>} />
      {isError && <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">Gagal memuat data.</div>}
      <DataTable columns={columns} data={users} loading={isLoading} page={meta?.page} totalPages={meta?.total_pages}
        onPageChange={setPage} searchValue={search} onSearchChange={(v) => { setSearch(v); setPage(1); }}
        searchPlaceholder="Cari nama pengguna atau nama..."         emptyTitle="Belum ada akun admin" />
      <UserForm open={formOpen} onClose={() => { setFormOpen(false); setEditData(null); }} editData={editData} onSuccess={onFormSuccess} />
      <ConfirmDialog open={!!deleteTarget} onOpenChange={(o) => { if (!o) setDeleteTarget(null); }}
        title="Hapus Admin" message={`Yakin ingin menghapus akun "${deleteTarget?.username}"?`} onConfirm={() => deleteMutation.mutate(deleteTarget?.id)} confirmLabel="Hapus" variant="danger" requirePassword />
    </div>
  );
}
