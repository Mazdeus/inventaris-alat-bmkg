import { useState, useEffect } from "react";
import { cn } from "@/lib/utils";
import { Search, ChevronLeft, ChevronRight, PackageOpen, Loader2, X } from "lucide-react";
import { TableSkeleton } from "./TableSkeleton";
import EmptyState from "./EmptyState";

/**
 * Tabel data reusable dengan search, pagination, loading, dan empty state.
 *
 * @param {object} props
 * @param {object[]} props.columns     - Definisi kolom: [{ key, header, render? }]
 * @param {object[]} props.data        - Array data yang akan ditampilkan
 * @param {boolean}  [props.loading]   - Tampilkan skeleton/loading bar saat loading
 * @param {number}   [props.page]      - Halaman saat ini (1-based)
 * @param {number}   [props.totalPages] - Total halaman
 * @param {function} [props.onPageChange] - Callback (page) saat ganti halaman
 * @param {string}   [props.searchValue]  - Nilai search input
 * @param {function} [props.onSearchChange] - Callback (value) saat search berubah
 * @param {string}   [props.searchPlaceholder] - Placeholder search input
 * @param {function} [props.onRowClick] - Callback (row) saat baris diklik
 * @param {string}   [props.emptyTitle] - Judul saat data kosong
 * @param {string}   [props.emptyMessage] - Pesan saat data kosong
 */
export default function DataTable({
  columns,
  data,
  loading = false,
  page,
  totalPages,
  onPageChange,
  searchValue,
  onSearchChange,
  searchPlaceholder = "Cari...",
  onRowClick,
  emptyTitle = "Tidak ada data",
  emptyMessage,
}) {
  const [inputPage, setInputPage] = useState(page ? String(page) : "");
  const [internalSearch, setInternalSearch] = useState(searchValue ?? "");
  const [isDebouncing, setIsDebouncing] = useState(false);

  useEffect(() => {
    setInputPage(page ? String(page) : "");
  }, [page]);

  useEffect(() => {
    setInternalSearch(searchValue ?? "");
  }, [searchValue]);

  useEffect(() => {
    if (internalSearch === (searchValue ?? "")) {
      setIsDebouncing(false);
      return;
    }
    setIsDebouncing(true);
    const timer = setTimeout(() => {
      onSearchChange?.(internalSearch);
      setIsDebouncing(false);
    }, 300);

    return () => clearTimeout(timer);
  }, [internalSearch]);

  const isBusy = loading || isDebouncing;

  /** Ganti halaman */
  const handlePage = (p) => {
    if (onPageChange && p >= 1 && p <= totalPages) {
      onPageChange(p);
    }
  };

  const handleInputSubmit = (e) => {
    e?.preventDefault?.();
    const p = parseInt(inputPage, 10);
    if (!isNaN(p) && p >= 1 && p <= totalPages && p !== page) {
      handlePage(p);
    } else {
      setInputPage(page ? String(page) : "");
    }
  };

  return (
    <div className="rounded-lg border border-gray-200 bg-white shadow-sm overflow-hidden">
      {/* Search bar */}
      {onSearchChange && (
        <div className="flex items-center border-b border-gray-100 px-4 py-3">
          <Search className="mr-2 h-4 w-4 shrink-0 text-gray-400" />
          <input
            type="text"
            placeholder={searchPlaceholder}
            value={internalSearch}
            onChange={(e) => setInternalSearch(e.target.value)}
            className="w-full text-sm outline-none placeholder:text-gray-400 bg-transparent"
          />
          {isBusy ? (
            <div className="ml-2 flex items-center gap-1.5 text-xs text-slate-500 shrink-0">
              <Loader2 className="h-4 w-4 animate-spin text-slate-600" />
              <span className="hidden sm:inline text-gray-400">Memuat...</span>
            </div>
          ) : internalSearch ? (
            <button
              type="button"
              onClick={() => {
                setInternalSearch("");
                onSearchChange?.("");
              }}
              className="ml-2 rounded-full p-0.5 text-gray-400 hover:bg-gray-100 hover:text-gray-600 transition"
              title="Hapus pencarian"
            >
              <X className="h-4 w-4" />
            </button>
          ) : null}
        </div>
      )}

      {/* Indeterminate loading bar di atas tabel */}
      {isBusy && (
        <div className="relative h-1 w-full overflow-hidden bg-slate-100">
          <div className="animate-indeterminate absolute inset-y-0 bg-slate-700 rounded-full" />
        </div>
      )}

      {/* Loading skeleton (hanya saat data awal masih kosong) */}
      {isBusy && data.length === 0 && <TableSkeleton rows={5} cols={columns.length} />}

      {/* Empty state (saat tidak ada data dan tidak sedang loading) */}
      {!isBusy && data.length === 0 && (
        <EmptyState icon={PackageOpen} title={emptyTitle} description={emptyMessage} />
      )}

      {/* Table (tetap tampil namun sedikit redup jika data sudah ada saat loading/search) */}
      {data.length > 0 && (
        <div className={cn("transition-opacity duration-200", isBusy && "opacity-50 pointer-events-none")}>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200 bg-gray-50 text-left">
                  {columns.map((col) => (
                    <th
                      key={col.key}
                      className="whitespace-nowrap px-4 py-3 font-semibold text-gray-600"
                    >
                      {col.header}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {data.map((row, idx) => (
                  <tr
                    key={row.id ?? idx}
                    onClick={() => onRowClick?.(row)}
                    className={cn(
                      "transition-colors",
                      onRowClick && "cursor-pointer hover:bg-slate-50"
                    )}
                  >
                    {columns.map((col) => (
                      <td key={col.key} className="px-4 py-3 text-gray-700">
                        {col.render ? col.render(row, idx) : row[col.key]}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {page !== undefined && totalPages !== undefined && totalPages > 1 && (
            <div className="flex flex-wrap items-center justify-between gap-2 border-t border-gray-100 px-4 py-3">
              <div className="flex items-center gap-3">
                <span className="text-xs text-gray-500">
                  Halaman <span className="font-semibold text-gray-700">{page}</span> dari{" "}
                  <span className="font-semibold text-gray-700">{totalPages}</span>
                </span>
                <form onSubmit={handleInputSubmit} className="flex items-center gap-1">
                  <span className="text-xs text-gray-300">|</span>
                  <label htmlFor="jump-page" className="text-xs text-gray-500">
                    Ke hal:
                  </label>
                  <input
                    id="jump-page"
                    type="number"
                    min={1}
                    max={totalPages}
                    value={inputPage}
                    onChange={(e) => setInputPage(e.target.value)}
                    onBlur={handleInputSubmit}
                    className="w-12 rounded border border-gray-300 bg-white px-1.5 py-0.5 text-center text-xs text-gray-700 outline-none transition focus:border-slate-500 focus:ring-1 focus:ring-slate-500"
                    placeholder={String(page)}
                  />
                </form>
              </div>
              <div className="flex items-center gap-1">
                <button
                  type="button"
                  onClick={() => handlePage(page - 1)}
                  disabled={page <= 1}
                  className="rounded-md border border-gray-200 px-2 py-1 text-xs transition hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-40"
                  title="Halaman Sebelumnya"
                >
                  <ChevronLeft className="h-3.5 w-3.5 text-gray-600" />
                </button>
                <button
                  type="button"
                  onClick={() => handlePage(page + 1)}
                  disabled={page >= totalPages}
                  className="rounded-md border border-gray-200 px-2 py-1 text-xs transition hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-40"
                  title="Halaman Berikutnya"
                >
                  <ChevronRight className="h-3.5 w-3.5 text-gray-600" />
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
