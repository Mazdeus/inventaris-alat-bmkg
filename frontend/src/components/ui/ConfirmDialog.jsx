import { useState, useEffect } from "react";
import { authApi } from "@/api/auth";

/**
 * Konfirmasi aksi berbahaya (hapus, approve, reject, cancel).
 *
 * @param {object} props
 * @param {boolean} props.open - Apakah dialog terbuka
 * @param {function} props.onOpenChange - Callback untuk mengubah state open
 * @param {string} props.title - Judul dialog
 * @param {string} props.message - Pesan konfirmasi
 * @param {function} props.onConfirm - Callback saat user mengkonfirmasi
 * @param {string} [props.confirmLabel="Hapus"] - Label tombol konfirmasi
 * @param {string} [props.variant="danger"] - Jenis tombol: "danger" | "default"
 * @param {boolean} [props.requirePassword=false] - Jika true, wajib masukkan password admin
 */
export function confirmAction({ title, message, confirmLabel = "Hapus", variant = "danger" } = {}) {
  return window.confirm(`${title}\n\n${message}`);
}

export function ConfirmDialog({
  open,
  onOpenChange,
  title,
  message,
  onConfirm,
  confirmLabel = "Hapus",
  variant = "danger",
  requirePassword = false,
}) {
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [verifying, setVerifying] = useState(false);

  // Reset state saat dialog dibuka
  useEffect(() => {
    if (open) {
      setPassword("");
      setError("");
      setVerifying(false);
    }
  }, [open]);

  if (!open) return null;

  async function handleConfirm() {
    if (requirePassword) {
      if (!password.trim()) {
        setError("Password admin wajib diisi.");
        return;
      }
      setVerifying(true);
      setError("");
      try {
        await authApi.verifyPassword(password);
        onConfirm?.();
        onOpenChange?.(false);
      } catch (err) {
        setError(err?.response?.data?.detail || "Password salah. Gagal memverifikasi.");
      } finally {
        setVerifying(false);
      }
    } else {
      onConfirm?.();
      onOpenChange?.(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-sm rounded-lg bg-white p-6 shadow-xl">
        <h3 className="text-lg font-semibold text-slate-800">{title}</h3>
        <p className="mt-2 text-sm text-gray-600">{message}</p>

        {requirePassword && (
          <div className="mt-4">
            <label className="mb-1 block text-sm font-medium text-gray-700">
              Password Admin <span className="text-red-500">*</span>
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => { setPassword(e.target.value); setError(""); }}
              onKeyDown={(e) => { if (e.key === "Enter") handleConfirm(); }}
              placeholder="Masukkan password admin"
              autoFocus
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-slate-400"
            />
            {error && <p className="mt-1 text-xs text-red-500">{error}</p>}
          </div>
        )}

        <div className="mt-4 flex justify-end gap-3">
          <button
            onClick={() => onOpenChange?.(false)}
            className="rounded-md border border-gray-300 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
          >
            Batal
          </button>
          <button
            onClick={handleConfirm}
            disabled={verifying}
            className={`rounded-md px-4 py-2 text-sm font-medium text-white disabled:cursor-not-allowed disabled:opacity-60 ${
              variant === "danger"
                ? "bg-red-600 hover:bg-red-700"
                : "bg-slate-800 hover:bg-slate-700"
            }`}
          >
            {verifying ? "Memverifikasi..." : confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
