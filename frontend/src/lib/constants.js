/**
 * Konstanta dan design tokens untuk seluruh aplikasi.
 * Warna, format, dan nilai tetap yang digunakan di banyak komponen.
 *
 * Nilai status internal (yang disimpan di backend/database) menggunakan Bahasa
 * Inggris. Label tampilan (Bahasa Indonesia) didefinisikan di STATUS_LABELS.
 */

/** Warna badge untuk status komponen inventaris */
export const STATUS_COLORS = {
  Available: "bg-emerald-100 text-emerald-800 border-emerald-300",
  "On Hold": "bg-amber-100 text-amber-800 border-amber-300",
  Borrowed: "bg-orange-100 text-orange-800 border-orange-300",
  Maintenance: "bg-blue-100 text-blue-800 border-blue-300",
  Broken: "bg-red-100 text-red-800 border-red-300",
  Deleted: "bg-gray-200 text-gray-500 border-gray-300",
  Transferred: "bg-purple-100 text-purple-800 border-purple-300",
};

/** Warna badge untuk status approval peminjaman */
export const APPROVAL_COLORS = {
  Approved: "bg-emerald-100 text-emerald-800",
  Pending: "bg-yellow-100 text-yellow-800",
  Rejected: "bg-red-100 text-red-800",
};

/** Warna badge untuk status transaksi peminjaman (backward compat) */
export const TRANSACTION_COLORS = {
  Borrowed: "bg-orange-100 text-orange-800",
  Returned: "bg-emerald-100 text-emerald-800",
  Cancelled: "bg-gray-100 text-gray-600",
};

/** Warna badge untuk status pengembalian */
export const RETURN_STATUS_COLORS = {
  Pending: "bg-amber-100 text-amber-800 border-amber-300",
  Completed: "bg-emerald-100 text-emerald-800 border-emerald-300",
  Cancelled: "bg-red-100 text-red-800 border-red-300",
};

/** Warna badge untuk status transaksi peminjaman (4 status terpadu) */
export const BORROW_STATUS_COLORS = {
  Pending: "bg-yellow-100 text-yellow-800 border-yellow-300",
  Borrowed: "bg-orange-100 text-orange-800 border-orange-300",
  Returned: "bg-emerald-100 text-emerald-800 border-emerald-300",
  Cancelled: "bg-gray-100 text-gray-600 border-gray-300",
};

/** Label Bahasa Indonesia untuk nilai status internal (English → tampilan) */
export const STATUS_LABELS = {
  // Status inventaris
  Available: "Tersedia",
  "On Hold": "Ditahan",
  Borrowed: "Dipinjam",
  Maintenance: "Perbaikan",
  Broken: "Rusak",
  Deleted: "Dihapuskan",
  Transferred: "Dilimpahkan",
  // Status transaksi peminjaman
  Pending: "Menunggu",
  Returned: "Dikembalikan",
  Cancelled: "Dibatalkan",
  // Status perpanjangan
  Approved: "Disetujui",
  Rejected: "Ditolak",
  // Status pengembalian
  Completed: "Selesai",
  // Pemeliharaan
  "In Progress": "Dalam Proses",
  // Kondisi pengembalian
  Good: "Baik",
  Damaged: "Rusak",
  // Tipe peminjam
  Internal: "Internal",
  External: "Eksternal",
};

/** Label Bahasa Indonesia untuk peran (role) */
export const ROLE_LABELS = {
  Admin: "Administrator",
  User: "Pengguna",
};

/** Warna untuk chart/pie di dashboard */
export const CHART_COLORS = {
  available: "#10b981",
  borrowed: "#f59e0b",
  maintenance: "#3b82f6",
  broken: "#ef4444",
  pending: "#eab308",
};

/** Format tanggal Indonesia (pakai date-fns) */
export const DATE_FORMAT = "dd MMMM yyyy";
export const DATETIME_FORMAT = "dd MMM yyyy, HH:mm";

/** Daftar nama bulan Indonesia (1-12) */
export const MONTHS = [
  "Januari", "Februari", "Maret", "April", "Mei", "Juni",
  "Juli", "Agustus", "September", "Oktober", "November", "Desember",
];

/** Daftar singkatan bulan (grafik) */
export const MONTHS_SHORT = [
  "Jan", "Feb", "Mar", "Apr", "Mei", "Jun",
  "Jul", "Agu", "Sep", "Okt", "Nov", "Des",
];

/** Lebar sidebar saat collapse (icon only) dan expand (icon + label) */
export const SIDEBAR_COLLAPSED_WIDTH = 64;
export const SIDEBAR_EXPANDED_WIDTH = 240;

/** Warna border kiri untuk StatCard berdasarkan status */
export const STAT_CARD_BORDER = {
  available: "border-l-emerald-500",
  borrowed: "border-l-orange-500",
  maintenance: "border-l-blue-500",
  broken: "border-l-red-500",
  default: "border-l-slate-400",
  pending: "border-l-yellow-500",
};
