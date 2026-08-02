import { cn } from "@/lib/utils";
import { STATUS_COLORS, APPROVAL_COLORS, TRANSACTION_COLORS, BORROW_STATUS_COLORS, RETURN_STATUS_COLORS, STATUS_LABELS } from "@/lib/constants";

/**
 * Peta konfigurasi warna badge.
 * Dipilih berdasarkan `type` prop.
 */
const COLOR_MAPS = {
  status: STATUS_COLORS,
  approval: APPROVAL_COLORS,
  transaction: TRANSACTION_COLORS,
  borrow: BORROW_STATUS_COLORS,
  return: RETURN_STATUS_COLORS,
  borrower: {
    Internal: "bg-blue-100 text-blue-800 border-blue-200",
    External: "bg-purple-100 text-purple-800 border-purple-200",
  },
};

/**
 * Komponen badge untuk menampilkan status/tipe dengan warna semantik.
 *
 * @param {object} props
 * @param {"status"|"approval"|"transaction"|"borrower"} [props.type="status"] - Kategori warna
 * @param {string} props.value - Nilai status (contoh: "Available", "Approved")
 * @param {string} [props.label] - Label tampilan (jika berbeda dari value)
 * @param {string} [props.className] - CSS class tambahan
 */
export default function StatusBadge({ type = "status", value, label, className }) {
  const map = COLOR_MAPS[type] || STATUS_COLORS;
  const colors = map[value] || "bg-gray-100 text-gray-600 border-gray-200";
  const display = label || STATUS_LABELS[value] || value || "-";

  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium",
        colors,
        className
      )}
    >
      {display}
    </span>
  );
}
