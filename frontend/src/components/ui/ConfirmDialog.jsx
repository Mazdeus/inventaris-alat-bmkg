/**
 * Dialog konfirmasi untuk aksi berbahaya (hapus, approve, reject, cancel).
 * Menggunakan AlertDialog dari shadcn/ui (akan ditambahkan via CLI).
 *
 * Untuk saat ini (sebelum shadcn setup), gunakan window.confirm sederhana.
 * Setelah shadcn terpasang, ganti dengan komponen AlertDialog.
 *
 * @param {object} props
 * @param {string} props.title - Judul dialog
 * @param {string} props.message - Pesan konfirmasi
 * @param {function} props.onConfirm - Callback saat user klik Ya/Konfirmasi
 * @param {string} [props.confirmLabel="Hapus"] - Label tombol konfirmasi
 * @param {string} [props.variant="danger"] - Jenis tombol: "danger" | "default"
 * @returns {boolean} true jika user konfirmasi
 */
export function confirmAction({ title, message, confirmLabel = "Hapus", variant = "danger" } = {}) {
  return window.confirm(`${title}\n\n${message}`);
}

/**
 * Komponen pembungkus yang akan diganti dengan AlertDialog shadcn/ui.
 * Digunakan untuk menghindari rewrite saat upgrade.
 */
export function ConfirmDialog({ open, onOpenChange, title, message, onConfirm, confirmLabel = "Hapus", variant = "danger" }) {
  if (!open) return null;

  const handleConfirm = () => {
    onConfirm();
    onOpenChange?.(false);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-sm rounded-lg bg-white p-6 shadow-xl">
        <h3 className="text-lg font-semibold text-slate-800">{title}</h3>
        <p className="mt-2 text-sm text-gray-600">{message}</p>
        <div className="mt-4 flex justify-end gap-3">
          <button
            onClick={() => onOpenChange?.(false)}
            className="rounded-md border border-gray-300 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
          >
            Batal
          </button>
          <button
            onClick={handleConfirm}
            className={`rounded-md px-4 py-2 text-sm font-medium text-white ${
              variant === "danger"
                ? "bg-red-600 hover:bg-red-700"
                : "bg-slate-800 hover:bg-slate-700"
            }`}
          >
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
