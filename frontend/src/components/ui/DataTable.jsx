import { cn } from "@/lib/utils";
import { Search, ChevronLeft, ChevronRight, PackageOpen } from "lucide-react";
import { TableSkeleton } from "./TableSkeleton";
import EmptyState from "./EmptyState";

/**
 * Tabel data reusable dengan search, pagination, loading, dan empty state.
 *
 * @param {object} props
 * @param {object[]} props.columns     - Definisi kolom: [{ key, header, render? }]
 * @param {object[]} props.data        - Array data yang akan ditampilkan
 * @param {boolean}  [props.loading]   - Tampilkan skeleton saat loading
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
  /** Ganti halaman */
  const handlePage = (p) => {
    if (onPageChange && p >= 1 && p <= totalPages) {
      onPageChange(p);
    }
  };

  return (
    <div className="rounded-lg border border-gray-200 bg-white">
      {/* Search bar */}
      {onSearchChange && (
        <div className="flex items-center border-b border-gray-100 px-4 py-3">
          <Search className="mr-2 h-4 w-4 text-gray-400" />
          <input
            type="text"
            placeholder={searchPlaceholder}
            value={searchValue ?? ""}
            onChange={(e) => onSearchChange(e.target.value)}
            className="w-full text-sm outline-none placeholder:text-gray-400"
          />
        </div>
      )}

      {/* Loading skeleton */}
      {loading && <TableSkeleton rows={5} cols={columns.length} />}

      {/* Empty state */}
      {!loading && data.length === 0 && (
        <EmptyState icon={PackageOpen} title={emptyTitle} description={emptyMessage} />
      )}

      {/* Table */}
      {!loading && data.length > 0 && (
        <>
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
                        {col.render ? col.render(row) : row[col.key]}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {page !== undefined && totalPages !== undefined && totalPages > 1 && (
            <div className="flex items-center justify-between border-t border-gray-100 px-4 py-3">
              <span className="text-xs text-gray-500">
                Halaman {page} dari {totalPages}
              </span>
              <div className="flex gap-1">
                <button
                  onClick={() => handlePage(page - 1)}
                  disabled={page <= 1}
                  className="rounded-md border border-gray-200 px-2 py-1 text-xs transition hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-40"
                >
                  <ChevronLeft className="h-3 w-3" />
                </button>
                <button
                  onClick={() => handlePage(page + 1)}
                  disabled={page >= totalPages}
                  className="rounded-md border border-gray-200 px-2 py-1 text-xs transition hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-40"
                >
                  <ChevronRight className="h-3 w-3" />
                </button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
