import { cn } from "@/lib/utils";

/**
 * Skeleton loading untuk tabel.
 * @param {object} props
 * @param {number} [props.rows=5] - Jumlah baris skeleton
 * @param {number} [props.cols=4] - Jumlah kolom skeleton
 */
export function TableSkeleton({ rows = 5, cols = 4 }) {
  return (
    <div className="space-y-3 p-4">
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="flex gap-4">
          {Array.from({ length: cols }).map((_, j) => (
            <div
              key={j}
              className="h-4 flex-1 animate-pulse rounded bg-gray-200"
              style={{ animationDelay: `${i * 100}ms` }}
            />
          ))}
        </div>
      ))}
    </div>
  );
}

/**
 * Skeleton loading untuk kartu dashboard.
 * @param {object} props
 * @param {number} [props.count=4] - Jumlah kartu skeleton
 */
export function CardSkeleton({ count = 4 }) {
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="animate-pulse rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
          <div className="mb-2 h-3 w-20 rounded bg-gray-200" />
          <div className="h-6 w-16 rounded bg-gray-200" />
        </div>
      ))}
    </div>
  );
}
