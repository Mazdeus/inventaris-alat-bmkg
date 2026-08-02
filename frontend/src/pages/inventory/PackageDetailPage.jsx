import { useParams, useNavigate, Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { inventoryApi } from "@/api/inventory";
import PageHeader from "@/components/ui/PageHeader";
import StatusBadge from "@/components/ui/StatusBadge";
import { TableSkeleton } from "@/components/ui/TableSkeleton";
import EmptyState from "@/components/ui/EmptyState";
import { formatDate } from "@/lib/formatters";
import { ArrowLeft, MapPin, Calendar, Image, Boxes, PackageOpen } from "lucide-react";

/**
 * Halaman detail satu paket inventaris.
 * Menampilkan info paket + tabel daftar komponen di dalamnya.
 * Route: /inventory/packages/:id
 */
export default function PackageDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();

  const { data, isLoading, isError } = useQuery({
    queryKey: ["package", id],
    queryFn: () => inventoryApi.getPackage(Number(id)),
    enabled: !!id,
  });

  const pkg = data?.data?.data;
  const components = pkg?.components || [];

  return (
    <div>
      {/* Back button */}
      <button
        onClick={() => navigate("/inventory/packages")}
        className="mb-4 flex items-center gap-1 text-sm text-gray-500 transition hover:text-slate-700"
      >
        <ArrowLeft className="h-4 w-4" />
        Kembali ke daftar paket
      </button>

      {/* Loading */}
      {isLoading && (
        <div className="space-y-4">
          <div className="h-8 w-48 animate-pulse rounded bg-gray-200" />
          <div className="h-40 animate-pulse rounded-lg bg-gray-200" />
          <TableSkeleton rows={3} cols={5} />
        </div>
      )}

      {/* Error */}
      {isError && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-6 text-center text-red-700">
          Gagal memuat data paket. Mungkin paket tidak ditemukan.
          <br />
          <button
            onClick={() => navigate("/inventory/packages")}
            className="mt-2 text-sm underline"
          >
            Kembali ke daftar paket
          </button>
        </div>
      )}

      {/* Data */}
      {!isLoading && !isError && pkg && (
        <>
          <PageHeader
            title={`Paket: ${pkg.box_number}`}
            description={`Detail paket inventaris dan daftar komponen di dalamnya`}
          />

          {/* Info card */}
          <div className="mb-6 grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
            {/* Foto */}
            <div className="rounded-lg border border-gray-200 bg-white p-4">
              <p className="mb-2 text-xs font-medium uppercase text-gray-500">Foto</p>
              {pkg.photo ? (
                <img
                  src={pkg.photo}
                  alt={pkg.box_number}
                  className="h-32 w-full rounded-md object-cover"
                  onError={(e) => {
                    e.target.style.display = "none";
                  }}
                />
              ) : (
                <div className="flex h-20 items-center justify-center rounded-md bg-gray-100">
                  <Image className="h-8 w-8 text-gray-300" />
                </div>
              )}
            </div>

            {/* Lokasi */}
            <div className="rounded-lg border border-gray-200 bg-white p-4">
              <p className="mb-2 text-xs font-medium uppercase text-gray-500">Lokasi</p>
              <div className="flex items-center gap-2">
                <MapPin className="h-4 w-4 text-gray-400" />
                <span className="text-sm font-medium text-slate-700">
                  {pkg.location || "Belum ditentukan"}
                </span>
              </div>
            </div>

            {/* Jumlah komponen */}
            <div className="rounded-lg border border-gray-200 bg-white p-4">
              <p className="mb-2 text-xs font-medium uppercase text-gray-500">Komponen</p>
              <div className="flex items-center gap-2">
                <Boxes className="h-4 w-4 text-gray-400" />
                <span className="text-2xl font-bold text-slate-800">
                  {components.length}
                </span>
              </div>
            </div>

            {/* Tanggal dibuat */}
            <div className="rounded-lg border border-gray-200 bg-white p-4">
              <p className="mb-2 text-xs font-medium uppercase text-gray-500">Dibuat</p>
              <div className="flex items-center gap-2">
                <Calendar className="h-4 w-4 text-gray-400" />
                <span className="text-sm font-medium text-slate-700">
                  {formatDate(pkg.created_at)}
                </span>
              </div>
            </div>
          </div>

          {/* Catatan */}
          {pkg.notes && (
            <div className="mb-6 rounded-lg border border-gray-200 bg-white p-4">
              <p className="mb-1 text-xs font-medium uppercase text-gray-500">Catatan</p>
              <p className="text-sm text-gray-700">{pkg.notes}</p>
            </div>
          )}

          {/* Daftar komponen */}
          <div className="rounded-lg border border-gray-200 bg-white">
            <div className="border-b border-gray-100 px-4 py-3">
              <h3 className="text-sm font-semibold text-gray-700">
                Daftar Komponen ({components.length})
              </h3>
            </div>

            {components.length === 0 ? (
              <EmptyState
                icon={PackageOpen}
                title="Belum ada komponen"
                description="Paket ini belum memiliki komponen. Tambahkan komponen melalui halaman Komponen Inventaris."
              />
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-gray-100 bg-gray-50 text-left">
                      <th className="px-4 py-3 font-semibold text-gray-600">Nama</th>
                      <th className="px-4 py-3 font-semibold text-gray-600">Merek</th>
                      <th className="px-4 py-3 font-semibold text-gray-600">Model</th>
                      <th className="px-4 py-3 font-semibold text-gray-600">Serial Number</th>
                      <th className="px-4 py-3 font-semibold text-gray-600">Jumlah</th>
                      <th className="px-4 py-3 font-semibold text-gray-600">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {components.map((comp) => (
                      <tr
                        key={comp.id}
                        onClick={() => navigate(`/inventory/components/${comp.id}`)}
                        className="cursor-pointer transition hover:bg-slate-50"
                      >
                        <td className="px-4 py-3 font-medium text-slate-800">
                          {comp.item_name}
                        </td>
                        <td className="px-4 py-3 text-gray-600">{comp.brand || "-"}</td>
                        <td className="px-4 py-3 text-gray-600">{comp.model || "-"}</td>
                        <td className="px-4 py-3 font-mono text-xs text-gray-600">
                          {comp.serial_number || "-"}
                        </td>
                        <td className="px-4 py-3">
                          <span className="inline-flex rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-600">
                            {comp.total_quantity ?? 0}
                          </span>
                        </td>
                        <td className="px-4 py-3">
                          <StatusBadge type="status" value={comp.status} />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}
