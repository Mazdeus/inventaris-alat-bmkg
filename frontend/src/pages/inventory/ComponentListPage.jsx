import { useState, useRef } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { inventoryApi } from "@/api/inventory";
import DataTable from "@/components/ui/DataTable";
import PageHeader from "@/components/ui/PageHeader";
import FilterBar from "@/components/ui/FilterBar";
import { ConfirmDialog } from "@/components/ui/ConfirmDialog";
import ComponentForm from "./ComponentForm";
import { Boxes, Plus, Pencil, Trash2, Download, Upload, Loader2, HelpCircle, X } from "lucide-react";

/**
 * Halaman daftar komponen inventaris.
 * Fitur: multi-filter (status, tahun), search, pagination, CRUD (Admin).
 */
export default function ComponentListPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { isAdmin } = useAuth();

  // Pagination, search, filter
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [filterYear, setFilterYear] = useState(null);
  const [filterDivision, setFilterDivision] = useState(null);

  // Modal form
  const [formOpen, setFormOpen] = useState(false);
  const [editData, setEditData] = useState(null);

  // Confirm delete
  const [deleteTarget, setDeleteTarget] = useState(null);

  // Import Excel
  const [importResult, setImportResult] = useState(null);
  const [importing, setImporting] = useState(false);
  const fileInputRef = useRef(null);

  // Template info modal
  const [showTemplateInfo, setShowTemplateInfo] = useState(false);

  // Fetch komponen
  const { data, isLoading, isError } = useQuery({
    queryKey: ["components", page, search, filterYear, filterDivision],
    queryFn: () =>
      inventoryApi.getComponents({
        page,
        size: 10,
        search: search || undefined,
        procurement_year: filterYear || undefined,
        division: filterDivision || undefined,
      }),
    keepPreviousData: true,
  });

  const components = data?.data?.data || [];
  const meta = data?.data?.meta;

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: (id) => inventoryApi.deleteComponent(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["components"] });
      setDeleteTarget(null);
    },
  });

  // Column definitions
  const columns = [
    {
      key: "photo",
      header: "Gambar",
      width: "w-16",
      render: (row) => (
        <div className="flex items-center">
          {row.photo_url ? (
            <img
              src={row.photo_url}
              alt={row.item_name}
              className="h-10 w-10 rounded-md border border-gray-200 object-cover"
              onError={(e) => { e.target.style.display = "none"; }}
            />
          ) : (
            <div className="flex h-10 w-10 items-center justify-center rounded-md border border-gray-200 bg-gray-50 text-gray-400">
              <Boxes className="h-5 w-5" />
            </div>
          )}
        </div>
      ),
    },
    {
      key: "item_name",
      header: "Nama Unit",
      render: (row) => (
        <div>
          <p className="font-medium text-slate-800">{row.item_name}</p>
          {row.brand && <p className="text-xs text-gray-400">{row.brand} {row.model ? `/ ${row.model}` : ""}</p>}
          {row.specifications && <p className="text-xs text-gray-400 mt-0.5 truncate max-w-48">{row.specifications}</p>}
        </div>
      ),
    },
    {
      key: "division",
      header: "Divisi",
      render: (row) => (
        <span className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${
          row.division === "Gempa Bumi" ? "bg-yellow-100 text-yellow-800" :
          row.division === "Tsunami" ? "bg-blue-100 text-blue-800" :
          row.division === "Percepatan Tanah" ? "bg-emerald-100 text-emerald-800" :
          "bg-gray-100 text-gray-600"
        }`}>{row.division || "-"}</span>
      ),
    },
    {
      key: "availability",
      header: "Stok",
      render: (row) => {
        const avail = row.available_quantity ?? 0;
        const total = row.total_quantity ?? 0;
        return (
          <div className="text-sm">
            <span
              className={
                avail > 0
                  ? "font-semibold text-emerald-600"
                  : "font-semibold text-red-500"
              }
            >
              {avail}
            </span>
            <span className="text-gray-400"> / {total}</span>
          </div>
        );
      },
    },
    {
      key: "procurement_year",
      header: "Tahun",
      render: (row) => row.procurement_year || "-",
    },
    {
      key: "actions",
      header: "Aksi",
      render: (row) =>
        isAdmin ? (
          <div className="flex gap-1">
            <button
              onClick={(e) => { e.stopPropagation(); openEdit(row); }}
              className="rounded-md p-1 text-blue-600 hover:bg-blue-50"
              title="Ubah"
            >
              <Pencil className="h-4 w-4" />
            </button>
            <button
              onClick={(e) => { e.stopPropagation(); setDeleteTarget(row); }}
              className="rounded-md p-1 text-red-600 hover:bg-red-50"
              title="Hapus"
            >
              <Trash2 className="h-4 w-4" />
            </button>
          </div>
        ) : null,
    },
  ];

  /** Filter definitions for FilterBar */
  const filters = [
    {
      label: "Divisi",
      key: "division",
      value: filterDivision,
      onChange: (v) => { setFilterDivision(v || null); setPage(1); },
      options: [
        { value: "Gempa Bumi", label: "Gempa Bumi" },
        { value: "Tsunami", label: "Tsunami" },
        { value: "Percepatan Tanah", label: "Percepatan Tanah" },
      ],
    },
    {
      label: "Tahun",
      key: "year",
      value: filterYear,
      onChange: (v) => { setFilterYear(v || null); setPage(1); },
      options: Array.from({ length: 8 }, (_, i) => {
        const y = new Date().getFullYear() - i;
        return { value: y, label: String(y) };
      }),
    },
  ];

  function openCreate() { setEditData(null); setFormOpen(true); }
  function openEdit(comp) { setEditData(comp); setFormOpen(true); }
  function onFormSuccess() { setFormOpen(false); setEditData(null);
    queryClient.invalidateQueries({ queryKey: ["components"] });
  }
  function handleDelete() { if (deleteTarget) deleteMutation.mutate(deleteTarget.id); }

  /** Download template Excel */
  async function handleDownloadTemplate() {
    try {
      const res = await inventoryApi.downloadTemplate();
      const blob = new Blob([res.data], { type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "template_komponen.xlsx";
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setImportResult({ error: "Gagal mengunduh template: " + (err.response?.data?.detail || err.message) });
    }
  }

  /** Upload & import Excel */
  async function handleImportFile(e) {
    const file = e.target.files?.[0];
    if (!file) return;
    setImporting(true);
    setImportResult(null);
    try {
      const res = await inventoryApi.importComponents(file);
      const data = res.data;
      setImportResult({ success: true, created: data.created, total_sheets: data.total_sheets, errors: data.errors || [] });
      queryClient.invalidateQueries({ queryKey: ["components"] });
    } catch (err) {
      setImportResult({ error: err.response?.data?.detail || err.response?.data?.message || "Gagal mengimpor file" });
    } finally {
      setImporting(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  }

  return (
    <div>
      <PageHeader
        title="Unit Inventaris"
        description="Kelola setiap unit inventaris"
        actions={
          isAdmin ? (
            <div className="flex items-center gap-2">
              <button onClick={handleDownloadTemplate}
                className="flex items-center gap-1 rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-700 hover:bg-gray-50">
                <Download className="h-4 w-4" /> Template Excel
              </button>
              <button onClick={() => setShowTemplateInfo(true)}
                className="rounded-md p-2 text-gray-400 hover:bg-gray-100 hover:text-gray-600"
                title="Info format template">
                <HelpCircle className="h-4 w-4" />
              </button>
              <label className="flex cursor-pointer items-center gap-1 rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-700 hover:bg-gray-50">
                <Upload className="h-4 w-4" /> Import Excel
                <input type="file" ref={fileInputRef} accept=".xlsx,.xlsm"
                  onChange={handleImportFile} className="hidden" />
              </label>
              <button onClick={openCreate} className="flex items-center gap-1 rounded-md bg-slate-800 px-3 py-2 text-sm font-medium text-white hover:bg-slate-700">
                <Plus className="h-4 w-4" /> Tambah Unit
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

      {/* Import progress/result */}
      {importing && (
        <div className="mb-4 flex items-center gap-2 rounded-lg border border-blue-200 bg-blue-50 px-4 py-3 text-sm text-blue-700">
          <Loader2 className="h-4 w-4 animate-spin" /> Mengimpor data dari Excel...
        </div>
      )}
      {importResult && (
        <div className={`mb-4 rounded-lg border px-4 py-3 text-sm ${importResult.success ? "border-emerald-200 bg-emerald-50 text-emerald-700" : "border-red-200 bg-red-50 text-red-700"}`}>
          {importResult.success ? (
            <div>
              <p className="font-medium">
                Impor selesai: {importResult.created} dari {importResult.total_sheets || 0} unit berhasil ditambahkan.
              </p>
              {importResult.errors?.length > 0 && (
                <div className="mt-2">
                  <p className="text-xs font-medium text-amber-700 mb-1">Peringatan ({importResult.errors.length}):</p>
                  <ul className="list-inside list-disc text-xs text-amber-700 space-y-0.5 max-h-40 overflow-y-auto">
                    {importResult.errors.map((e, i) => <li key={i}>{e}</li>)}
                  </ul>
                </div>
              )}
            </div>
          ) : (
            <div>
              <p className="font-medium">{importResult.error}</p>
              {importResult.errors?.length > 0 && (
                <ul className="mt-2 list-inside list-disc text-xs space-y-0.5 max-h-40 overflow-y-auto">
                  {importResult.errors.map((e, i) => <li key={i}>{e}</li>)}
                </ul>
              )}
            </div>
          )}
          <button onClick={() => setImportResult(null)} className="mt-2 text-xs underline">Tutup</button>
        </div>
      )}

      <FilterBar filters={filters} />

      <DataTable
        columns={columns}
        data={components}
        loading={isLoading}
        page={meta?.page}
        totalPages={meta?.total_pages}
        onPageChange={setPage}
        searchValue={search}
        onSearchChange={(v) => { setSearch(v); setPage(1); }}
        searchPlaceholder="Cari nama, merek, atau nomor seri..."
        onRowClick={(row) => navigate(`/inventory/components/${row.id}`)}
        emptyTitle="Belum ada unit"
        emptyMessage="Klik 'Tambah Unit' untuk menambahkan unit inventaris pertama."
      />

      <ComponentForm open={formOpen} onClose={() => { setFormOpen(false); setEditData(null); }}
        editData={editData} onSuccess={onFormSuccess} />

      {/* Template Info Modal */}
      {showTemplateInfo && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="mx-4 w-full max-w-lg rounded-xl bg-white shadow-xl">
            <div className="flex items-center justify-between border-b px-6 py-4">
              <h3 className="text-base font-semibold text-gray-800">Format Template Excel</h3>
              <button onClick={() => setShowTemplateInfo(false)} className="rounded-md p-1 text-gray-400 hover:bg-gray-100 hover:text-gray-600">
                <X className="h-5 w-5" />
              </button>
            </div>
            <div className="px-6 py-4 text-sm text-gray-600 space-y-3 max-h-96 overflow-y-auto">
              <p>Template Excel memiliki <b>6 sheet</b>:</p>
              <ol className="list-decimal list-inside space-y-1 ml-2">
                <li><b>Petunjuk</b>: berisi petunjuk pengisian (tidak diproses saat import).</li>
                <li><b>Unit_1</b> s.d <b>Unit_5</b>: formulir untuk mengisi data unit. Bisa ditambah sheet baru (Unit_6, Unit_7, dst) untuk lebih dari 5 unit.</li>
              </ol>
              <div>
                <p className="font-medium text-gray-800 mb-1">Isi setiap sheet Unit:</p>
                <ul className="list-disc list-inside space-y-1 ml-2">
                  <li>Kolom A = label (jangan diubah). Kolom B = isi nilai.</li>
                  <li>Field bertanda <b className="text-red-600">merah</b> = wajib diisi.</li>
                  <li>Divisi sudah disediakan dropdown.</li>
                  <li>Isi <b>Nomor Seri</b> setiap barang (jumlah harus = Jumlah Total). Biarkan kosong jika barang tidak memiliki SN: sistem akan mengisi <b>'-'</b> otomatis.</li>
                  <li>Nomor seri <b>tidak boleh duplikat</b> (kecuali tanda '-' untuk barang tanpa SN).</li>
                </ul>
              </div>
              <p className="text-xs text-gray-400">Sheet Unit_1 diisi contoh di Petunjuk. Download template untuk melihat langsung.</p>
            </div>
            <div className="border-t px-6 py-3 flex justify-end">
              <button onClick={() => setShowTemplateInfo(false)} className="rounded-md bg-slate-800 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700">Mengerti</button>
            </div>
          </div>
        </div>
      )}

      <ConfirmDialog open={!!deleteTarget} onOpenChange={(o) => { if (!o) setDeleteTarget(null); }}
        title="Hapus Unit"
        message={`Yakin ingin menghapus unit "${deleteTarget?.item_name}"? Unit yang sedang dipinjam tidak bisa dihapus.`}
        onConfirm={handleDelete} confirmLabel="Hapus" variant="danger" />
    </div>
  );
}
