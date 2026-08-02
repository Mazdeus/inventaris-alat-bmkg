/**
 * Baris filter dengan beberapa select dropdown inline.
 *
 * @param {object} props
 * @param {object[]} props.filters - Array konfigurasi filter:
 *   [{ label, key, options: [{value, label}], value, onChange }]
 * @param {React.ReactNode} [props.children] - Konten tambahan (tombol, dll.)
 */
export default function FilterBar({ filters, children }) {
  return (
    <div className="mb-4 flex flex-wrap items-center gap-3">
      {filters.map((filter) => (
        <div key={filter.key} className="flex items-center gap-2">
          <label className="text-xs font-medium text-gray-500">{filter.label}</label>
          <select
            value={filter.value ?? ""}
            onChange={(e) => filter.onChange(e.target.value || undefined)}
            className="rounded-md border border-gray-300 bg-white px-2 py-1.5 text-xs text-gray-700 outline-none focus:border-slate-400 focus:ring-1 focus:ring-slate-400"
          >
            <option value="">Semua</option>
            {filter.options.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>
      ))}
      {children && <div className="ml-auto flex gap-2">{children}</div>}
    </div>
  );
}
