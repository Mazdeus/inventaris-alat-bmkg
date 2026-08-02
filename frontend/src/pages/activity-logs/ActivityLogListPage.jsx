import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { activityLogsApi } from "@/api/activityLogs";
import DataTable from "@/components/ui/DataTable";
import PageHeader from "@/components/ui/PageHeader";
import { formatDateTime } from "@/lib/formatters";
import { Eye } from "lucide-react";
import ActivityLogDetailModal from "@/components/activity-logs/ActivityLogDetailModal";

export default function ActivityLogListPage() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [selectedLog, setSelectedLog] = useState(null);

  const { data, isLoading, isError } = useQuery({
    queryKey: ["activityLogs", page, search, startDate, endDate],
    queryFn: () => activityLogsApi.getLogs({
      page, size: 20,
      user_id: undefined,
      start_date: startDate || undefined,
      end_date: endDate || undefined,
    }),
    keepPreviousData: true,
  });

  const logs = data?.data?.data || [];
  const meta = data?.data?.meta;

  const columns = [
    { key: "created_at", header: "Waktu", render: (r) => <span className="text-xs whitespace-nowrap">{formatDateTime(r.created_at)}</span> },
    { key: "user", header: "Pengguna", render: (r) => <span className="font-mono text-xs font-medium">{r.user?.username || "-"}</span> },
    { key: "activity", header: "Aktivitas", render: (r) => <span className="text-sm">{r.activity}</span> },
    { key: "reference", header: "Referensi", render: (r) => r.reference_table ? <span className="inline-flex rounded bg-gray-100 px-1.5 py-0.5 text-xs text-gray-600">{r.reference_table} #{r.reference_id}</span> : <span className="text-xs text-gray-400">-</span> },
    { key: "ip_address", header: "IP", render: (r) => <span className="font-mono text-xs text-gray-500">{r.ip_address || "-"}</span> },
    { key: "actions", header: "Aksi", render: (r) => (
      <button onClick={(e) => { e.stopPropagation(); setSelectedLog(r); }}
        className="rounded-md p-1 text-blue-600 hover:bg-blue-50" title="Detail">
        <Eye className="h-4 w-4" />
      </button>
    )},
  ];

  return (
    <div>
      <PageHeader title="Log Aktivitas"         description="Seluruh aktivitas pengguna dalam sistem (hanya baca)" />
      {isError && <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">Gagal memuat data.</div>}
      <div className="mb-4 flex flex-wrap items-center gap-3">
        <input type="datetime-local" value={startDate} onChange={(e) => { setStartDate(e.target.value); setPage(1); }}
          className="rounded-md border border-gray-300 px-2 py-1 text-xs text-gray-600" />
        <span className="text-xs text-gray-400">s/d</span>
        <input type="datetime-local" value={endDate} onChange={(e) => { setEndDate(e.target.value); setPage(1); }}
          className="rounded-md border border-gray-300 px-2 py-1 text-xs text-gray-600" />
      </div>
      <DataTable columns={columns} data={logs} loading={isLoading} page={meta?.page} totalPages={meta?.total_pages}
        onPageChange={setPage} searchValue={search} onSearchChange={(v) => { setSearch(v); setPage(1); }}
        searchPlaceholder="Cari aktivitas..." emptyTitle="Belum ada log" emptyMessage="Aktivitas akan tercatat otomatis saat user melakukan aksi." />

      <ActivityLogDetailModal log={selectedLog} onClose={() => setSelectedLog(null)} />
    </div>
  );
}
