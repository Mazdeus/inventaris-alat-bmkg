import { X } from "lucide-react";

/**
 * Modal dialog reusable — untuk form tambah/edit.
 *
 * @param {object} props
 * @param {boolean} props.open - Apakah modal terbuka
 * @param {function} props.onClose - Callback saat modal ditutup
 * @param {string} props.title - Judul modal
 * @param {React.ReactNode} props.children - Konten modal
 * @param {string} [props.maxWidth="max-w-lg"] - Lebar maksimal modal
 */
export default function Modal({ open, onClose, title, children, maxWidth = "max-w-lg" }) {
  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center overflow-y-auto bg-black/50 p-6 pt-20">
      <div className={`w-full ${maxWidth} rounded-lg bg-white shadow-xl`}>
        {/* Header */}
        <div className="flex items-center justify-between border-b border-gray-200 px-6 py-4">
          <h2 className="text-lg font-semibold text-slate-800">{title}</h2>
          <button
            onClick={onClose}
            className="rounded-md p-1 text-gray-400 transition hover:bg-gray-100 hover:text-gray-600"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Konten */}
        <div className="px-6 py-4">{children}</div>
      </div>
    </div>
  );
}
