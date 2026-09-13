import { cn } from "@/lib/utils";

/**
 * Kartu statistik ringkasan modern (Inspirasi Rochainx & ERP Logo).
 *
 * @param {object} props
 * @param {string} props.title - Judul metrik
 * @param {string|number} props.value - Nilai yang ditampilkan
 * @param {React.ComponentType} [props.icon] - Komponen ikon dari lucide-react
 * @param {string} [props.iconColor] - Warna ikon (contoh: "text-emerald-600")
 * @param {string} [props.iconBg] - Latar ikon (contoh: "bg-emerald-50")
 * @param {string} [props.colorClass] - Class warna border kiri (opsional)
 * @param {string} [props.subtitle] - Teks kecil di bawah nilai
 * @param {string} [props.badge] - Badge label kecil di samping subtitle
 * @param {string} [props.className] - CSS class tambahan
 */
export default function StatCard({
  title,
  value,
  icon: Icon,
  iconColor = "text-slate-600",
  iconBg = "bg-slate-50",
  colorClass,
  subtitle,
  badge,
  className,
}) {
  return (
    <div
      className={cn(
        "group relative flex flex-col justify-between rounded-2xl border border-slate-200/80 bg-white p-5 shadow-xs transition-all duration-200 hover:border-slate-300 hover:shadow-sm",
        colorClass && `border-l-[3px] ${colorClass}`,
        className
      )}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <p className="text-xs font-medium text-slate-500 tracking-wide">{title}</p>
          <p className="mt-1.5 text-2xl font-bold tracking-tight text-slate-900">
            {typeof value === "number" ? value.toLocaleString("id-ID") : (value ?? 0)}
          </p>
        </div>
        {Icon && (
          <div
            className={cn(
              "flex h-10 w-10 shrink-0 items-center justify-center rounded-xl transition-transform duration-200 group-hover:scale-105",
              iconBg
            )}
          >
            <Icon className={cn("h-5 w-5", iconColor)} />
          </div>
        )}
      </div>
      {(subtitle || badge) && (
        <div className="mt-3.5 flex items-center justify-between border-t border-slate-100/80 pt-2.5 text-xs">
          {subtitle && (
            <span className="text-[11px] font-normal text-slate-400 leading-tight">
              {subtitle}
            </span>
          )}
          {badge && (
            <span className="ml-auto inline-flex items-center rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-medium text-slate-600">
              {badge}
            </span>
          )}
        </div>
      )}
    </div>
  );
}
