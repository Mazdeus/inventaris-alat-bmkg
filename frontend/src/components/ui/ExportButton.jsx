import { jsPDF } from "jspdf";
import autoTable from "jspdf-autotable";
import * as XLSX from "xlsx";
import { FileDown, FileSpreadsheet } from "lucide-react";

/**
 * Tombol export data tabel ke PDF atau Excel.
 *
 * @param {object} props
 * @param {object[]} props.data   - Array data yang mau di-export
 * @param {object[]} props.columns - Definisi kolom: [{ key, header, render? }]
 * @param {string}   props.filename - Nama file (tanpa ekstensi)
 * @param {"pdf"|"excel"} props.type - Jenis export
 * @param {string}   [props.title] - Judul laporan (hanya untuk PDF)
 */
export default function ExportButton({ data, columns, filename, type, title }) {
  const icon = type === "pdf" ? <FileDown className="h-4 w-4" /> : <FileSpreadsheet className="h-4 w-4" />;
  const label = type === "pdf" ? "PDF" : "Excel";

  function handleExport() {
    if (type === "pdf") exportPDF(data, columns, filename, title);
    else exportExcel(data, columns, filename);
  }

  return (
    <button onClick={handleExport} disabled={!data.length}
      className="flex items-center gap-1 rounded-md border border-gray-300 bg-white px-3 py-1.5 text-xs font-medium text-gray-600 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-40">
      {icon} {label}
    </button>
  );
}

/** Export data ke PDF */
function exportPDF(data, columns, filename, title) {
  const doc = new jsPDF();
  doc.setFontSize(14);
  doc.text(title || "Laporan BMKG", 14, 15);
  doc.setFontSize(10);
  doc.text(`Tanggal: ${new Date().toLocaleDateString("id-ID")}`, 14, 22);

  const head = [columns.map((c) => c.header)];
  const body = data.map((row) =>
    columns.map((col) => {
      const val = col.render ? col.render(row) : row[col.key];
      // Extract text from React elements
      if (typeof val === "object" && val?.props?.children) return String(val.props.children);
      return val ?? "";
    })
  );

  autoTable(doc, { head, body, startY: 28, styles: { fontSize: 8 }, headStyles: { fillColor: [30, 41, 59] } });
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
  const wb = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(wb, ws, "Data");
  XLSX.writeFile(wb, `${filename}.xlsx`);
}
