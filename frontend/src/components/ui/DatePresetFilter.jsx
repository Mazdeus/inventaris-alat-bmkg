import { useState, useEffect } from "react";
import { Calendar } from "lucide-react";

function getTodayStr() {
  const d = new Date();
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function getYesterdayStr() {
  const d = new Date();
  d.setDate(d.getDate() - 1);
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

/**
 * Filter tanggal cepat dengan preset: Semua, Hari Ini, Kemarin, Kustom
 *
 * @param {object} props
 * @param {string} props.startDate - tanggal awal (YYYY-MM-DD)
 * @param {string} props.endDate - tanggal akhir (YYYY-MM-DD)
 * @param {function} props.onChange - callback(startDate, endDate)
 */
export default function DatePresetFilter({ startDate = "", endDate = "", onChange }) {
  const today = getTodayStr();
  const yesterday = getYesterdayStr();

  // Tentukan preset aktif berdasarkan startDate dan endDate
  const getActivePreset = () => {
    if (!startDate && !endDate) return "all";
    if (startDate === today && endDate === today) return "today";
    if (startDate === yesterday && endDate === yesterday) return "yesterday";
    return "custom";
  };

  const [activePreset, setActivePreset] = useState(getActivePreset);

  useEffect(() => {
    setActivePreset(getActivePreset());
  }, [startDate, endDate]);

  const handleSelectPreset = (preset) => {
    setActivePreset(preset);
    if (preset === "all") {
      onChange("", "");
    } else if (preset === "today") {
      onChange(today, today);
    } else if (preset === "yesterday") {
      onChange(yesterday, yesterday);
    }
  };

  return (
    <div className="flex flex-wrap items-center gap-2">
      {/* Preset buttons */}
      <div className="inline-flex rounded-lg border border-slate-200 bg-slate-50 p-0.5 text-xs">
        <button
          type="button"
          onClick={() => handleSelectPreset("all")}
          className={`rounded-md px-2.5 py-1 font-medium transition-colors ${
            activePreset === "all"
              ? "bg-white text-slate-900 shadow-sm"
              : "text-slate-600 hover:text-slate-900"
          }`}
        >
          Semua
        </button>
        <button
          type="button"
          onClick={() => handleSelectPreset("today")}
          className={`rounded-md px-2.5 py-1 font-medium transition-colors ${
            activePreset === "today"
              ? "bg-white text-slate-900 shadow-sm"
              : "text-slate-600 hover:text-slate-900"
          }`}
        >
          Hari Ini
        </button>
        <button
          type="button"
          onClick={() => handleSelectPreset("yesterday")}
          className={`rounded-md px-2.5 py-1 font-medium transition-colors ${
            activePreset === "yesterday"
              ? "bg-white text-slate-900 shadow-sm"
              : "text-slate-600 hover:text-slate-900"
          }`}
        >
          Kemarin
        </button>
        <button
          type="button"
          onClick={() => handleSelectPreset("custom")}
          className={`flex items-center gap-1 rounded-md px-2.5 py-1 font-medium transition-colors ${
            activePreset === "custom"
              ? "bg-white text-slate-900 shadow-sm"
              : "text-slate-600 hover:text-slate-900"
          }`}
        >
          <Calendar className="h-3 w-3" />
          Pilih Tanggal
        </button>
      </div>

      {/* Date inputs (hanya muncul saat mode Pilih Tanggal dipilih atau rentang tanggal kustom aktif) */}
      {activePreset === "custom" && (
        <div className="flex items-center gap-1.5 animate-fadeIn">
          <input
            type="date"
            value={startDate}
            onChange={(e) => onChange(e.target.value, endDate)}
            className="rounded-md border border-slate-300 bg-white px-2 py-1 text-xs text-slate-700 shadow-sm outline-none focus:border-slate-500 focus:ring-1 focus:ring-slate-500"
          />
          <span className="text-xs text-slate-400">s/d</span>
          <input
            type="date"
            value={endDate}
            onChange={(e) => onChange(startDate, e.target.value)}
            className="rounded-md border border-slate-300 bg-white px-2 py-1 text-xs text-slate-700 shadow-sm outline-none focus:border-slate-500 focus:ring-1 focus:ring-slate-500"
          />
        </div>
      )}
    </div>
  );
}
