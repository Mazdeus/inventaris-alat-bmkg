import { Link } from "react-router-dom";
import {
  ArrowRight, Wrench, RotateCcw, Trash2, UserCog,
  BookOpen, Send, Circle
} from "lucide-react";
import { STATUS_LABELS } from "@/lib/constants";

/** Warna badge per status */
const STATUS_BADGE_COLORS = {
  Available: "bg-emerald-100 text-emerald-800",
  Borrowed: "bg-orange-100 text-orange-800",
  Maintenance: "bg-blue-100 text-blue-800",
  Broken: "bg-red-100 text-red-800",
  Dihapuskan: "bg-gray-200 text-gray-500",
  Dilimpahkan: "bg-purple-100 text-purple-800",
};

/** Warna dot timeline per status */
const STATUS_DOT_COLORS = {
  Available: "bg-emerald-500 ring-emerald-200",
  Borrowed: "bg-orange-500 ring-orange-200",
  Maintenance: "bg-blue-500 ring-blue-200",
  Broken: "bg-red-500 ring-red-200",
  Dihapuskan: "bg-gray-400 ring-gray-200",
  Dilimpahkan: "bg-purple-500 ring-purple-200",
};

/** Icon dan label per sumber */
const SOURCE_META = {
  BORROW: { icon: BookOpen, label: "Peminjaman", color: "text-orange-600" },
  RETURN: { icon: RotateCcw, label: "Pengembalian", color: "text-emerald-600" },
  MAINTENANCE: { icon: Wrench, label: "Perawatan", color: "text-blue-600" },
  HANDOVER: { icon: Send, label: "Pelimpahan", color: "text-purple-600" },
  ADMIN_TOGGLE: { icon: UserCog, label: "Admin (Manual)", color: "text-gray-600" },
  DELETE: { icon: Trash2, label: "Penghapusan", color: "text-red-500" },
};

/**
 * Timeline vertikal riwayat status barang.
 * Menampilkan perubahan status dari waktu ke waktu dengan garis penghubung.
 */
export default function ItemStatusTimeline({ history = [], loading = false, error = false }) {
  if (loading) {
    return <p className="text-sm text-gray-400 py-4 text-center">Memuat riwayat...</p>;
  }

  if (error) {
    return <p className="text-sm text-red-500 py-4 text-center">Gagal memuat riwayat</p>;
  }

  if (!history || history.length === 0) {
    return <p className="text-sm text-gray-400 py-4 text-center">Belum ada riwayat perubahan status</p>;
  }

  return (
    <div className="relative pl-6">
      {/* Vertical line */}
      <div className="absolute left-[11px] top-2 bottom-2 w-0.5 bg-gray-200" />

      {history.map((h, idx) => {
        const fromLabel = STATUS_LABELS[h.from_status] || h.from_status || "-";
        const toLabel = STATUS_LABELS[h.to_status] || h.to_status;
        const sourceMeta = SOURCE_META[h.source] || { icon: Circle, label: h.source_label || h.source, color: "text-gray-500" };
        const SourceIcon = sourceMeta.icon;
        const dotColor = STATUS_DOT_COLORS[h.to_status] || "bg-gray-400 ring-gray-200";
        const badgeColor = STATUS_BADGE_COLORS[h.to_status] || "bg-gray-100 text-gray-700";

        return (
          <div key={h.id} className="relative pb-4 last:pb-0">
            {/* Dot */}
            <div className={`absolute -left-[21px] top-1.5 h-3.5 w-3.5 rounded-full ring-2 ${dotColor}`} />

            {/* Card */}
            <div className="rounded-md border border-gray-200 bg-white p-3 text-xs shadow-sm">
              {/* Header: date + source icon */}
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-gray-400">
                  {new Date(h.created_at).toLocaleString("id-ID", {
                    day: "numeric",
                    month: "short",
                    year: "numeric",
                    hour: "2-digit",
                    minute: "2-digit",
                  })}
                </span>
                <span className={`flex items-center gap-1 font-medium ${sourceMeta.color}`}>
                  <SourceIcon className="h-3.5 w-3.5" />
                  {sourceMeta.label}
                </span>
              </div>

              {/* Status transition */}
              <div className="flex items-center gap-1.5 mb-1.5">
                <span className="rounded-full bg-gray-100 px-1.5 py-0.5 text-[10px] font-medium text-gray-600">
                  {fromLabel}
                </span>
                <ArrowRight className="h-3 w-3 text-gray-400 flex-shrink-0" />
                <span className={`rounded-full px-1.5 py-0.5 text-[10px] font-medium ${badgeColor}`}>
                  {toLabel}
                </span>
              </div>

              {/* User info */}
              {h.user_name && (
                <p className="text-gray-500 mb-0.5">Oleh: {h.user_name}</p>
              )}

              {/* Notes */}
              {h.notes && (
                <p className="text-gray-500 italic">"{h.notes}"</p>
              )}

              {/* Transaction links */}
              {(h.borrow_transaction_id || h.return_id) && (
                <div className="mt-1.5 flex gap-3 border-t border-gray-100 pt-1.5">
                  {h.borrow_transaction_id && (
                    <Link
                      to={`/borrow/transactions/${h.borrow_transaction_id}`}
                      target="_blank"
                      className="text-blue-600 hover:underline text-[10px] font-medium"
                    >
                      Peminjaman #{h.borrow_transaction_id}
                    </Link>
                  )}
                  {h.return_id && (
                    <Link
                      to={`/returns/${h.return_id}`}
                      target="_blank"
                      className="text-emerald-600 hover:underline text-[10px] font-medium"
                    >
                      Pengembalian #{h.return_id}
                    </Link>
                  )}
                </div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
