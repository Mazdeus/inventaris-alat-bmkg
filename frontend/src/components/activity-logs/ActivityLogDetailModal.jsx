import { useQuery } from "@tanstack/react-query";
import Modal from "@/components/ui/Modal";
import StatusBadge from "@/components/ui/StatusBadge";
import { borrowApi } from "@/api/borrow";
import { returnsApi } from "@/api/returns";
import { maintenanceApi } from "@/api/maintenance";
import { inventoryApi } from "@/api/inventory";
import { formatDateTime, formatDate } from "@/lib/formatters";
import { User, Clock, Activity, FileText, MapPin, Monitor, Link2, Loader2, Calendar, CalendarDays, Hash, Package } from "lucide-react";

/**
 * Modal untuk menampilkan detail log aktivitas + referensi terkait.
 */
export default function ActivityLogDetailModal({ log, onClose }) {
  if (!log) return null;

  const metadataObj = parseMetadata(log.extra_data);

  return (
    <Modal open={!!log} onClose={onClose} title="Detail Log Aktivitas" maxWidth="max-w-xl">
      <div className="space-y-4">
        {/* ID */}
        <div className="flex items-center gap-3">
          <FileText className="h-4 w-4 text-gray-400 shrink-0" />
          <div>
            <p className="text-xs text-gray-500 uppercase">ID Log</p>
            <p className="text-sm font-medium text-slate-700">#{log.id}</p>
          </div>
        </div>

        {/* User */}
        <div className="flex items-center gap-3">
          <User className="h-4 w-4 text-gray-400 shrink-0" />
          <div>
            <p className="text-xs text-gray-500 uppercase">Pengguna</p>
            <p className="text-sm font-medium text-slate-700">
              {log.user?.full_name || "-"} ({log.user?.username || "-"})
            </p>
          </div>
        </div>

        {/* Waktu */}
        <div className="flex items-center gap-3">
          <Clock className="h-4 w-4 text-gray-400 shrink-0" />
          <div>
            <p className="text-xs text-gray-500 uppercase">Waktu</p>
            <p className="text-sm font-medium text-slate-700">{formatDateTime(log.created_at)}</p>
          </div>
        </div>

        {/* Aktivitas */}
        <div className="flex items-start gap-3">
          <Activity className="h-4 w-4 text-gray-400 shrink-0 mt-0.5" />
          <div>
            <p className="text-xs text-gray-500 uppercase">Aktivitas</p>
            <p className="text-sm text-slate-700">{log.activity}</p>
          </div>
        </div>

        {/* IP Address */}
        {log.ip_address && (
          <div className="flex items-center gap-3">
            <MapPin className="h-4 w-4 text-gray-400 shrink-0" />
            <div>
              <p className="text-xs text-gray-500 uppercase">IP Address</p>
              <p className="font-mono text-sm text-slate-700">{log.ip_address}</p>
            </div>
          </div>
        )}

        {/* User Agent */}
        {log.user_agent && (
          <div className="flex items-center gap-3">
            <Monitor className="h-4 w-4 text-gray-400 shrink-0" />
            <div>
              <p className="text-xs text-gray-500 uppercase">User Agent</p>
              <p className="text-xs text-gray-600 break-all">{log.user_agent}</p>
            </div>
          </div>
        )}

        {/* Referensi + Detail */}
        {log.reference_table && log.reference_id && (
          <ReferenceDetail reference_table={log.reference_table} reference_id={log.reference_id} />
        )}

        {/* Metadata (detail tambahan) */}
        {metadataObj && (
          <div className="rounded-lg border border-gray-200 bg-gray-50 p-3">
            <p className="text-xs text-gray-500 uppercase mb-2">Detail Tambahan</p>
            <pre className="text-xs text-gray-700 whitespace-pre-wrap font-mono">{JSON.stringify(metadataObj, null, 2)}</pre>
          </div>
        )}

        {/* Tombol tutup */}
        <div className="flex justify-end pt-2">
          <button onClick={onClose} className="rounded-md border border-gray-300 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50">
            Tutup
          </button>
        </div>
      </div>
    </Modal>
  );
}

// ─────────────────────────────────────────────
// Komponen internal: fetch + tampilkan detail referensi
// ─────────────────────────────────────────────

const TABLE_LABELS = {
  borrow_transactions: "Transaksi Peminjaman",
  returns: "Pengembalian",
  maintenance: "Pemeliharaan",
  inventory_components: "Unit",
};

function ReferenceDetail({ reference_table, reference_id }) {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["refDetail", reference_table, reference_id],
    queryFn: async () => {
      switch (reference_table) {
        case "borrow_transactions": {
          const res = await borrowApi.getTransaction(reference_id);
          return { type: "borrow", data: res.data?.data };
        }
        case "returns": {
          const res = await returnsApi.getReturn(reference_id);
          return { type: "return", data: res.data?.data };
        }
        case "maintenance": {
          const res = await maintenanceApi.getMaintenance(reference_id);
          return { type: "maintenance", data: res.data?.data };
        }
        case "inventory_components": {
          const res = await inventoryApi.getComponent(reference_id);
          return { type: "component", data: res.data?.data };
        }
        default:
          return null;
      }
    },
    enabled: !!(reference_table && reference_id),
    staleTime: 2 * 60_000,
  });

  const label = TABLE_LABELS[reference_table] || reference_table;

  // Divider
  return (
    <>
      <hr className="border-gray-200" />

      {/* Judul referensi */}
      <div className="flex items-center gap-3">
        <Link2 className="h-4 w-4 text-gray-400 shrink-0" />
        <div>
          <p className="text-xs text-gray-500 uppercase">Referensi</p>
          <p className="text-sm font-medium text-slate-700">{label} #{reference_id}</p>
        </div>
      </div>

      {isLoading && (
        <div className="flex items-center gap-2 pl-7 text-xs text-gray-400">
          <Loader2 className="h-3 w-3 animate-spin" /> Memuat...
        </div>
      )}

      {isError && (
        <p className="pl-7 text-xs text-red-500">Gagal memuat detail.</p>
      )}

      {data?.type === "borrow" && <BorrowInfo tx={data.data} />}
      {data?.type === "return" && <ReturnInfo ret={data.data} />}
      {data?.type === "maintenance" && <MaintenanceInfo maint={data.data} />}
      {data?.type === "component" && <ComponentInfo comp={data.data} />}
    </>
  );
}

function BorrowInfo({ tx }) {
  if (!tx) return null;
  const details = tx.details || [];
  return (
    <>
      <Row icon={User} label="Peminjam" value={tx.borrower?.borrower_name} />
      <Row icon={Calendar} label="Tanggal Pinjam" value={formatDate(tx.borrow_date)} />
      <Row icon={CalendarDays} label="Rencana Kembali" value={formatDate(tx.expected_return_date)} />
      <div className="flex items-center gap-3">
        <div className="w-4 shrink-0" />
        <div className="flex items-center gap-2">
          <StatusBadge type="borrow" value={tx.status} />
        </div>
      </div>
      {details.length > 0 && (
        <div className="pl-7">
          <p className="text-xs text-gray-400 mb-1.5">{details.length} komponen dipinjam</p>
          <div className="divide-y divide-gray-100 rounded border border-gray-100">
            {details.map((d, i) => (
              <div key={i} className="flex items-center justify-between px-2.5 py-1.5 text-xs">
                <span className="font-medium text-slate-700 truncate mr-2">{d.component?.item_name || "-"}</span>
                <span className="text-gray-400 shrink-0">×{d.quantity}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </>
  );
}

function ReturnInfo({ ret }) {
  if (!ret) return null;
  const details = ret.details || [];
  return (
    <>
      <Row icon={User} label="Peminjam" value={ret.borrower_name} />
      <Row icon={CalendarDays} label="Tanggal Kembali" value={formatDate(ret.return_date)} />
      <Row icon={User} label="Diterima Oleh" value={ret.received_by} />
      {details.length > 0 && (
        <div className="pl-7">
          <p className="text-xs text-gray-400 mb-1.5">{details.length} komponen dikembalikan</p>
          <div className="divide-y divide-gray-100 rounded border border-gray-100">
            {details.map((d, i) => (
              <div key={i} className="flex items-center justify-between px-2.5 py-1.5 text-xs">
                <span className="font-medium text-slate-700 truncate mr-2">{d.component?.item_name || "-"}</span>
                <span className="text-gray-400 shrink-0">×{d.quantity}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </>
  );
}

function MaintenanceInfo({ maint }) {
  if (!maint) return null;
  const comp = maint.component;
  const itemSns = maint.items?.filter((it) => it.serial_number).map((it) => it.serial_number) || [];
  return (
    <>
      <Row icon={Package} label="Unit" value={comp?.item_name} />
      {comp?.serial_number && <Row icon={Hash} label="Nomor Seri" value={comp.serial_number} />}
      {itemSns.length > 0 && <Row icon={Hash} label="SN Barang Dirawat" value={itemSns.join(", ")} long />}
      <Row icon={Calendar} label="Tanggal Mulai" value={formatDate(maint.start_date)} />
      {maint.end_date && <Row icon={CalendarDays} label="Tanggal Selesai" value={formatDate(maint.end_date)} />}
      <Row icon={Activity} label="Status" value={maint.status} />
      {maint.description && <Row icon={FileText} label="Deskripsi" value={maint.description} long />}
    </>
  );
}

function ComponentInfo({ comp }) {
  if (!comp) return null;
  return (
    <>
      <Row icon={Package} label="Nama Unit" value={comp.item_name} />
      <Row icon={Hash} label="Merek / Model" value={[comp.brand, comp.model].filter(Boolean).join(" / ") || "-"} />
      <Row icon={Activity} label="Status" value={<StatusBadge type="status" value={comp.status} />} isBadge />
    </>
  );
}

// ─────────────────────────────────────────────

function Row({ icon: Icon, label, value, long }) {
  return (
    <div className="flex items-start gap-3">
      <Icon className="h-4 w-4 text-gray-400 shrink-0 mt-px" />
      <div className="min-w-0">
        <p className="text-xs text-gray-400 uppercase">{label}</p>
        <p className={`text-sm text-slate-700 ${long ? "break-words" : "truncate"}`}>
          {value || "-"}
        </p>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────

/** Parse metadata JSON string ke object. Return null jika gagal atau kosong. */
function parseMetadata(value) {
  if (!value) return null;
  try {
    const parsed = JSON.parse(value);
    return Object.keys(parsed).length > 0 ? parsed : null;
  } catch {
    return null;
  }
}
