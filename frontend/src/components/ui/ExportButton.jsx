import { useState } from "react";
import { jsPDF } from "jspdf";
import autoTable from "jspdf-autotable";
import * as XLSX from "xlsx";
import { FileDown, FileSpreadsheet, Loader2 } from "lucide-react";
import { toast } from "sonner";

/**
 * Tombol export data tabel ke PDF atau Excel.
 * Mendukung data langsung (array) atau fungsi async fetchData untuk mengambil seluruh data lintas halaman.
 *
 * @param {object} props
 * @param {object[]} [props.data]       - Array data langsung (fallback)
 * @param {() => Promise<object[]>} [props.fetchData] - Fungsi async pengambil seluruh data filter
 * @param {object[]} props.columns     - Definisi kolom: [{ key, header, render? }]
 * @param {string}   props.filename    - Nama file (tanpa ekstensi)
 * @param {"pdf"|"excel"} props.type   - Jenis export
 * @param {string}   [props.title]     - Judul laporan (hanya untuk PDF)
 */
export default function ExportButton({ data, fetchData, columns, filename, type, title }) {
  const [isExporting, setIsExporting] = useState(false);

  const icon = isExporting ? (
    <Loader2 className="h-4 w-4 animate-spin text-slate-500" />
  ) : type === "pdf" ? (
    <FileDown className="h-4 w-4" />
  ) : (
    <FileSpreadsheet className="h-4 w-4" />
  );

  const label = isExporting ? "Mengekspor..." : type === "pdf" ? "PDF" : "Excel";

  async function handleExport() {
    if (isExporting) return;

    if (fetchData) {
      try {
        setIsExporting(true);
        const rows = await fetchData();
        if (!rows || rows.length === 0) {
          toast.info("Tidak ada data untuk diekspor");
          return;
        }
        if (type === "pdf") {
          exportPDF(rows, columns, filename, title);
        } else {
          exportExcel(rows, columns, filename);
        }
        const txCount = rows.filter((r) => !r._isSubRow).length;
        toast.success(`Berhasil mengekspor ${txCount} data (${type.toUpperCase()})`);
      } catch (err) {
        console.error("Export error:", err);
        toast.error("Gagal mengekspor data: " + (err.message || "Terjadi kesalahan"));
      } finally {
        setIsExporting(false);
      }
    } else if (data && data.length > 0) {
      if (type === "pdf") exportPDF(data, columns, filename, title);
      else exportExcel(data, columns, filename);
    }
  }

  const isDisabled = isExporting || (!fetchData && (!data || data.length === 0));

  return (
    <button
      type="button"
      onClick={handleExport}
      disabled={isDisabled}
      className="flex items-center gap-1.5 rounded-md border border-gray-300 bg-white px-3 py-1.5 text-xs font-medium text-gray-700 hover:bg-gray-50 active:bg-gray-100 transition-colors disabled:cursor-not-allowed disabled:opacity-50 shadow-sm"
      title={`Ekspor seluruh data ke ${type.toUpperCase()}`}
    >
      {icon} {label}
    </button>
  );
}

/** Export data ke PDF */
function exportPDF(data, columns, filename, title) {
  const useLandscape = columns.length > 7;
  const doc = new jsPDF({
    orientation: useLandscape ? "landscape" : "portrait",
    unit: "mm",
    format: "a4",
  });
  doc.setFontSize(14);
  doc.text(title || "Laporan BMKG", 14, 15);
  doc.setFontSize(10);
  doc.text(`Tanggal: ${new Date().toLocaleDateString("id-ID")}`, 14, 22);

  const head = [columns.map((c) => c.header)];
  const body = [];

  data.forEach((row) => {
    if (row._isSubRow) {
      // Baris sub-row (hanya kolom yang TIDAK di-span oleh baris induk)
      const subCells = [];
      columns.forEach((col) => {
        if (!row._spanKeys || !row._spanKeys.includes(col.key)) {
          const val = col.render ? col.render(row) : row[col.key];
          subCells.push(typeof val === "object" && val?.props?.children ? String(val.props.children) : (val ?? ""));
        }
      });
      body.push(subCells);
    } else if (row._rowSpan && row._rowSpan > 1) {
      // Baris induk dengan rowSpan
      const mainCells = [];
      columns.forEach((col) => {
        const val = col.render ? col.render(row) : row[col.key];
        const textVal = typeof val === "object" && val?.props?.children ? String(val.props.children) : (val ?? "");
        if (row._spanKeys && row._spanKeys.includes(col.key)) {
          mainCells.push({
            content: textVal,
            rowSpan: row._rowSpan,
            styles: { valign: "middle" },
          });
        } else {
          mainCells.push(textVal);
        }
      });
      body.push(mainCells);
    } else {
      // Baris biasa (1 transaksi 1 baris)
      const cells = columns.map((col) => {
        const val = col.render ? col.render(row) : row[col.key];
        if (typeof val === "object" && val?.props?.children) return String(val.props.children);
        return val ?? "";
      });
      body.push(cells);
    }
  });

  autoTable(doc, {
    head,
    body,
    startY: 28,
    styles: { fontSize: useLandscape ? 7 : 8, cellPadding: 1.5, overflow: "linebreak", valign: "middle" },
    headStyles: { fillColor: [30, 41, 59] },
    columnStyles: { text: { cellWidth: "wrap" } },
  });
  doc.save(`${filename}.pdf`);
}

/** Export data ke Excel */
function exportExcel(data, columns, filename) {
  const rows = data.map((row) => {
    const obj = {};
    columns.forEach((col) => {
      const val = col.render ? col.render(row) : row[col.key];
      obj[col.header] = typeof val === "object" && val?.props?.children ? String(val.props.children) : (val ?? "");
    });
    return obj;
  });
  const ws = XLSX.utils.json_to_sheet(rows);

  // Buat merge range untuk baris yang memiliki _rowSpan
  const merges = [];
  data.forEach((row, idx) => {
    const rIndex = idx + 1; // 1-based index (0 adalah header tabel)
    if (row._rowSpan && row._rowSpan > 1) {
      columns.forEach((col, cIdx) => {
        if (row._spanKeys && row._spanKeys.includes(col.key)) {
          merges.push({
            s: { r: rIndex, c: cIdx },
            e: { r: rIndex + row._rowSpan - 1, c: cIdx },
          });
        }
      });
    }
  });

  if (merges.length > 0) {
    ws["!merges"] = merges;
  }

  const wb = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(wb, ws, "Data");
  XLSX.writeFile(wb, `${filename}.xlsx`);
}
