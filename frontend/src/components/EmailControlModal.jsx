import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import {
  getReminderStatus,
  testSmtp,
  triggerDueCheck,
  getReminderLogs,
} from "@/api/reminders";
import { useAuth } from "@/contexts/AuthContext";
import {
  X,
  Mail,
  Send,
  RefreshCw,
  Clock,
  History,
} from "lucide-react";
import { toast } from "sonner";

export default function EmailControlModal({ open, onClose }) {
  const { user } = useAuth();
  const [testEmail, setTestEmail] = useState(user?.email || "");
  const [forceTrigger, setForceTrigger] = useState(false);

  const [showLogs, setShowLogs] = useState(false);

  // Fetch SMTP status
  const { data: statusData } = useQuery({
    queryKey: ["reminderStatus"],
    queryFn: getReminderStatus,
    enabled: open,
  });

  // Fetch recent logs
  const { data: logsData, refetch: refetchLogs } = useQuery({
    queryKey: ["reminderLogs"],
    queryFn: () => getReminderLogs({ size: 5 }),
    enabled: open && showLogs,
  });

  // Test SMTP Mutation
  const testMutation = useMutation({
    mutationFn: (email) => testSmtp(email),
    onSuccess: (res) => {
      toast.success(res.message || "Email uji coba berhasil dikirim!");
      if (showLogs) refetchLogs();
    },
    onError: (err) => {
      toast.error(
        err?.response?.data?.detail || "Gagal mengirim email uji coba."
      );
    },
  });

  // Trigger Due Check Mutation
  const triggerMutation = useMutation({
    mutationFn: (force) => triggerDueCheck(force),
    onSuccess: (res) => {
      const { emails_sent, processed_transactions, skipped_duplicates } = res.data || {};
      toast.success(
        `Pindai selesai: ${emails_sent} email terkirim, ${processed_transactions} transaksi diproses (${skipped_duplicates} dilewati karena sudah dikirim hari ini).`
      );
      if (showLogs) refetchLogs();
    },
    onError: (err) => {
      toast.error(
        err?.response?.data?.detail || "Gagal menjalankan pemindaian pengingat."
      );
    },
  });

  if (!open) return null;

  const smtpInfo = statusData?.data || {};
  const logs = logsData?.data || [];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4 backdrop-blur-sm">
      <div className="w-full max-w-lg rounded-2xl bg-white shadow-xl border border-slate-100 overflow-hidden">
        {/* Header Minimalis */}
        <div className="flex items-center justify-between border-b border-slate-100 px-5 py-3.5 bg-slate-50/50">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-600 text-white">
              <Mail className="h-4 w-4" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-slate-800">
                Pengaturan Notifikasi Email
              </h3>
              <div className="flex items-center gap-1.5 text-[11px] text-slate-500">
                <span className="inline-block h-1.5 w-1.5 rounded-full bg-emerald-500"></span>
                <span>Pengirim: {smtpInfo.smtp_user || "Belum Terkonfigurasi"}</span>
                <span className="text-slate-300">•</span>
                <span>Cron: {smtpInfo.cron_schedule || "08:00 WIB"}</span>
              </div>

            </div>
          </div>
          <button
            onClick={onClose}
            className="rounded-lg p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-600"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Body Form Ringkas */}
        <div className="p-5 space-y-4 text-xs">
          {/* Section 1: Uji Coba Kirim Email */}
          <div className="rounded-xl border border-slate-200 bg-white p-3.5 shadow-sm">
            <label className="block font-medium text-slate-700 mb-1.5">
              1. Tes Kirim Email (SMTP Test)
            </label>
            <div className="flex gap-2">
              <input
                type="email"
                value={testEmail}
                onChange={(e) => setTestEmail(e.target.value)}
                placeholder="Email Admin tujuan (fadhilcr1@gmail.com)"
                className="flex-1 rounded-lg border border-slate-300 px-3 py-1.5 text-xs text-slate-800 placeholder-slate-400 focus:border-blue-500 focus:outline-none"
              />
              <button
                onClick={() => testMutation.mutate(testEmail)}
                disabled={testMutation.isPending || !testEmail}
                className="flex items-center gap-1 rounded-lg bg-blue-600 px-3 py-1.5 font-medium text-white hover:bg-blue-700 disabled:opacity-50"
              >
                {testMutation.isPending ? (
                  <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                ) : (
                  <Send className="h-3.5 w-3.5" />
                )}
                <span>Kirim Tes</span>
              </button>
            </div>
          </div>

          {/* Section 2: Pemindaian Massal */}
          <div className="rounded-xl border border-slate-200 bg-white p-3.5 shadow-sm space-y-2">
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium text-slate-700">2. Pindai Transaksi Sekarang</p>
                <p className="text-[11px] text-slate-400 mt-0.5">
                  Memeriksa otomatis pinjaman H-2, Hari-H, dan Terlambat
                </p>
              </div>
              <button
                onClick={() => triggerMutation.mutate(forceTrigger)}
                disabled={triggerMutation.isPending}
                className="flex items-center gap-1.5 rounded-lg bg-slate-800 px-3 py-1.5 font-medium text-white hover:bg-slate-700 disabled:opacity-50"
              >
                {triggerMutation.isPending ? (
                  <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                ) : (
                  <RefreshCw className="h-3.5 w-3.5" />
                )}
                <span>Pindai Sekarang</span>
              </button>
            </div>

            <label className="flex items-center gap-2 text-[11px] text-slate-500 cursor-pointer pt-1">
              <input
                type="checkbox"
                checked={forceTrigger}
                onChange={(e) => setForceTrigger(e.target.checked)}
                className="rounded border-slate-300 text-blue-600 focus:ring-0"
              />
              <span>Paksa kirim ulang (meskipun sudah dikirim hari ini)</span>
            </label>
          </div>

          {/* Section 3: Riwayat Log Notifikasi (Collapsible) */}
          <div>
            <button
              onClick={() => {
                setShowLogs(!showLogs);
                if (!showLogs) refetchLogs();
              }}
              className="flex items-center gap-1.5 text-xs font-medium text-blue-600 hover:text-blue-700"
            >
              <History className="h-3.5 w-3.5" />
              <span>{showLogs ? "Sembunyikan Riwayat Log" : "Lihat 5 Riwayat Email Terakhir"}</span>
            </button>

            {showLogs && (
              <div className="mt-2 rounded-lg border border-slate-200 bg-slate-50 p-2.5 space-y-1.5 max-h-40 overflow-y-auto">
                {logs.length === 0 ? (
                  <p className="text-[11px] text-slate-400 text-center py-2">Belum ada riwayat pengiriman.</p>
                ) : (
                  logs.map((log) => (
                    <div
                      key={log.id}
                      className="flex items-center justify-between text-[11px] bg-white p-2 rounded border border-slate-100"
                    >
                      <div className="truncate max-w-[280px]">
                        <span className="font-semibold text-slate-700">
                          {log.transaction_number ? `[${log.transaction_number}] ` : ""}
                        </span>
                        <span className="text-slate-600">{log.subject}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span
                          className={`rounded px-1.5 py-0.2 text-[10px] font-semibold ${
                            log.status === "success"
                              ? "bg-emerald-100 text-emerald-700"
                              : "bg-red-100 text-red-700"
                          }`}
                        >
                          {log.status === "success" ? "Sukses" : "Gagal"}
                        </span>
                        <span className="text-slate-400 text-[10px]">
                          {log.sent_at ? new Date(log.sent_at).toLocaleTimeString("id-ID", { hour: "2-digit", minute: "2-digit" }) : ""}
                        </span>
                      </div>
                    </div>
                  ))
                )}
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="flex justify-end border-t border-slate-100 bg-slate-50/50 px-5 py-2.5">
          <button
            onClick={onClose}
            className="rounded-lg bg-white border border-slate-200 px-3.5 py-1.5 text-xs font-medium text-slate-600 hover:bg-slate-100 shadow-sm"
          >
            Tutup
          </button>
        </div>
      </div>
    </div>
  );
}
