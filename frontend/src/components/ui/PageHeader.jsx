/**
 * Header halaman dengan judul, deskripsi opsional, dan slot aksi.
 *
 * @param {object} props
 * @param {string} props.title - Judul halaman
 * @param {string} [props.description] - Deskripsi di bawah judul
 * @param {React.ReactNode} [props.actions] - Tombol/elemen aksi di kanan header
 */
export default function PageHeader({ title, description, actions }) {
  return (
    <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <h1 className="text-xl font-bold text-slate-800">{title}</h1>
        {description && <p className="mt-1 text-sm text-gray-500">{description}</p>}
      </div>
      {actions && <div className="flex flex-wrap gap-2">{actions}</div>}
    </div>
  );
}
