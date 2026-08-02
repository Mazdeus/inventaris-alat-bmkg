import { cn } from "@/lib/utils";

/**
 * Kartu statistik ringkasan.
 * Menampilkan satu metrik (judul, angka, ikon opsional) dengan border kiri berwarna.
 *
 * @param {object} props
 * @param {string} props.title - Judul metrik (contoh: "Total Komponen")
 * @param {string|number} props.value - Nilai yang ditampilkan besar
 * @param {React.ComponentType} [props.icon] - Komponen ikon dari lucide-react
 * @param {string} [props.colorClass="border-l-slate-400"] - Class warna border kiri
 * @param {string} [props.subtitle] - Teks kecil opsional di bawah nilai
 * @param {string} [props.className] - CSS class tambahan
 */
export default function StatCard({
  title,
  value,
  icon: Icon,
  colorClass = "border-l-slate-400",
  subtitle,
  className,
}) {
  return (
    <div
      className={cn(
        "rounded-lg border border-gray-200 bg-white p-4 shadow-sm transition-shadow hover:shadow-md",
        "border-l-4",
        colorClass,
        className
      )}
    >
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs font-medium uppercase tracking-wide text-gray-500">{title}</p>
          <p className="mt-1 text-2xl font-bold text-slate-800">{value}</p>
          {subtitle && <p className="mt-1 text-xs text-gray-400">{subtitle}</p>}
        </div>
        {Icon && <Icon className="h-8 w-8 text-gray-300" />}
      </div>
    </div>
  );
}
