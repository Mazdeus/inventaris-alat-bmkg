import { useState } from "react";
import { useQuery, keepPreviousData } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { activityLogsApi } from "@/api/activityLogs";
import DataTable from "@/components/ui/DataTable";
import PageHeader from "@/components/ui/PageHeader";
import { formatDateTime } from "@/lib/formatters";
import {
  Boxes, ClipboardList, Users, UserCog, ArrowLeftRight,
  RotateCcw, Wrench, Send, LogIn, FileCheck,
} from "lucide-react";

/**
 * Mapping reference_table → { icon, label, linkBuilder }
 * Dipakai untuk menampilkan icon aktivitas dan link ke transaksi terkait.
 */
const REFERENCE_META = {
  inventory_components: {
    icon: Boxes,
    label: "Unit Inventaris",
    link: (id) => (id ? `/inventory/components/${id}` : "/inventory/components"),
  },
  officers: { icon: ClipboardList, label: "Petugas", link: () => "/officers" },
  borrowers: { icon: Users, label: "Peminjam", link: () => "/borrowers" },
  users: { icon: UserCog, label: "Akun Admin", link: () => "/users" },
  borrow_transactions: {
    icon: ArrowLeftRight,
    label: "Peminjaman",
    link: (id) => `/borrow/transactions/${id}`,
  },
  returns: { icon: RotateCcw, label: "Pengembalian", link: (id) => `/returns/${id}` },
  maintenance: { icon: Wrench, label: "Pemeliharaan", link: () => "/maintenance" },
  handovers: { icon: Send, label: "Pelimpahan", link: (id) => `/handovers/${id}` },
};

/** Login tidak punya reference_table — pakai icon login */
function getActivityMeta(log) {
  if (!log.reference_table) {
    return { icon: LogIn, label: null, link: null };
  }
  return REFERENCE_META[log.reference_table] || { icon: FileCheck, label: null, link: null };
}

export default function ActivityLogListPage() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");

  const { data, isLoading, isFetching, isError } = useQuery({
    queryKey: ["activityLogs", page, search, startDate, endDate],
    queryFn: () => activityLogsApi.getLogs({
      page, size: 20,
      user_id: undefined,
      search: search || undefined,
      start_date: startDate || undefined,
      end_date: endDate || undefined,
    }),
    placeholderData: keepPreviousData,
  });

  const logs = data?.data?.data || [];
  const meta = data?.data?.meta;

  const columns = [
    {
      key: "activity",
      header: "Aktivitas",
      render: (r) => {
        const { icon: Icon } = getActivityMeta(r);
        return (
          <span className="flex items-center gap-2">
            <span className="flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-md bg-slate-100 text-slate-600">
              <Icon className="h-4 w-4" />
            </span>
            <span className="text-sm text-slate-700">{r.activity}</span>
          </span>
        );
      },
    },
    {
      key: "created_at",
      header: "Waktu",
      render: (r) => (
        <span className="text-xs whitespace-nowrap text-slate-500">{formatDateTime(r.created_at)}</span>
      ),
    },
    {
      key: "user",
      header: "Pengguna",
      render: (r) => (
        <span className="font-mono text-xs font-medium text-slate-700">
          {r.user?.full_name || r.user?.username || "-"}
        </span>
      ),
    },
    {
      key: "ip_address",
      header: "IP Address",
      render: (r) => (
        <span className="font-mono text-xs text-gray-500">{r.ip_address || "-"}</span>
      ),
    },
    {
      key: "reference",
      header: "Referensi",
      render: (r) => {
        const { link } = getActivityMeta(r);
        if (link && r.reference_id) {
          return (
            <Link
              to={link(r.reference_id)}
              onClick={(e) => e.stopPropagation()}
              className="inline-flex items-center gap-1 rounded-md bg-blue-50 px-2 py-1 text-xs font-medium text-blue-600 hover:bg-blue-100 hover:text-blue-700"
            >
              Buka Transaksi
            </Link>
          );
        }
        if (link) {
          return (
            <Link
              to={link(r.reference_id)}
              onClick={(e) => e.stopPropagation()}
              className="inline-flex items-center gap-1 rounded-md bg-blue-50 px-2 py-1 text-xs font-medium text-blue-600 hover:bg-blue-100 hover:text-blue-700"
            >
              Lihat
            </Link>
          );
        }
        return <span className="text-xs text-gray-400">-</span>;
      },
    },
  ];

  return (
    <div>
      <PageHeader title="Log Aktivitas" description="Seluruh aktivitas pengguna dalam sistem (hanya baca)" />
      {isError && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          Gagal memuat data. Pastikan backend berjalan.
        </div>
      )}
      <div className="mb-4 flex flex-wrap items-center gap-3">
        <input type="datetime-local" value={startDate} onChange={(e) => { setStartDate(e.target.value); setPage(1); }}
          className="rounded-md border border-gray-300 px-2 py-1 text-xs text-gray-600" />
        <span className="text-xs text-gray-400">s/d</span>
        <input type="datetime-local" value={endDate} onChange={(e) => { setEndDate(e.target.value); setPage(1); }}
          className="rounded-md border border-gray-300 px-2 py-1 text-xs text-gray-600" />
      </div>
      <DataTable columns={columns} data={logs} loading={isLoading || isFetching} page={meta?.page} totalPages={meta?.total_pages}
        onPageChange={setPage} searchValue={search} onSearchChange={(v) => { setSearch(v); setPage(1); }}
        searchPlaceholder="Cari aktivitas, nama staf, atau modul..." emptyTitle="Belum ada log" emptyMessage="Aktivitas akan tercatat otomatis saat user melakukan aksi." />
    </div>
  );
}
