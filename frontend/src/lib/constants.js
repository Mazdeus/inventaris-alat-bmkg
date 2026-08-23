/**
 * Konstanta dan design tokens untuk seluruh aplikasi.
 * Warna, format, dan nilai tetap yang digunakan di banyak komponen.
 */

/** Warna badge untuk status komponen inventaris */
export const STATUS_COLORS = {
  Available: "bg-emerald-100 text-emerald-800 border-emerald-300",
  Ditahan: "bg-amber-100 text-amber-800 border-amber-300",
  Borrowed: "bg-orange-100 text-orange-800 border-orange-300",
  Maintenance: "bg-blue-100 text-blue-800 border-blue-300",
  Broken: "bg-red-100 text-red-800 border-red-300",
  Dihapuskan: "bg-gray-200 text-gray-500 border-gray-300",
  Dilimpahkan: "bg-purple-100 text-purple-800 border-purple-300",
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
  "Menunggu": "bg-amber-100 text-amber-800 border-amber-300",
  "Selesai": "bg-emerald-100 text-emerald-800 border-emerald-300",
  "Dibatalkan": "bg-red-100 text-red-800 border-red-300",
};

/** Warna badge untuk status transaksi peminjaman (4 status terpadu, Bahasa Indonesia) */
export const BORROW_STATUS_COLORS = {
  Menunggu: "bg-yellow-100 text-yellow-800 border-yellow-300",
  Dipinjam: "bg-orange-100 text-orange-800 border-orange-300",
  Dikembalikan: "bg-emerald-100 text-emerald-800 border-emerald-300",
  Dibatalkan: "bg-gray-100 text-gray-600 border-gray-300",
};

/** Label Bahasa Indonesia untuk nilai status (backend → frontend display) */
export const STATUS_LABELS = {
  // Status inventaris
  Available: "Tersedia",
  Ditahan: "Ditahan",
  Borrowed: "Dipinjam",
  Maintenance: "Perbaikan",
  Broken: "Rusak",
  Dihapuskan: "Dihapuskan",
  Dilimpahkan: "Dilimpahkan",
  // Approval (keep backward compatibility)
  Approved: "Disetujui",
  Pending: "Menunggu",
  Rejected: "Ditolak",
  // Transaksi terpadu (baru)
  Menunggu: "Menunggu",
  Dipinjam: "Dipinjam",
  Dikembalikan: "Dikembalikan",
  Dibatalkan: "Dibatalkan",
  // Transaksi (keep backward compatibility)
  Returned: "Dikembalikan",
  Cancelled: "Dibatalkan",
  // Tipe peminjam
  Internal: "Internal",
  External: "Eksternal",
  // Perawatan
  "In Progress": "Dalam Proses",
  Completed: "Selesai",
  // Pengembalian
  "Menunggu": "Menunggu",
  Selesai: "Selesai",
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
