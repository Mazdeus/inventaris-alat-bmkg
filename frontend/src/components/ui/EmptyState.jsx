import { cn } from "@/lib/utils";

/**
 * Tampilan saat data kosong (empty state).
 *
 * @param {object} props
 * @param {React.ComponentType} [props.icon] - Komponen ikon lucide-react
 * @param {string} [props.title="Tidak ada data"] - Judul pesan
 * @param {string} [props.description] - Deskripsi tambahan
 * @param {string} [props.className] - CSS class tambahan
 */
export default function EmptyState({
  icon: Icon,
  title = "Tidak ada data",
  description,
  className,
}) {
  return (
    <div className={cn("flex flex-col items-center justify-center py-16 text-center", className)}>
      {Icon && <Icon className="mb-3 h-12 w-12 text-gray-300" />}
      <h3 className="text-base font-semibold text-gray-500">{title}</h3>
      {description && <p className="mt-1 max-w-sm text-sm text-gray-400">{description}</p>}
    </div>
  );
}
