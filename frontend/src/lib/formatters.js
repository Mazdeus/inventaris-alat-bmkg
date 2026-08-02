import { format, parseISO } from "date-fns";
import { id } from "date-fns/locale";
import { DATE_FORMAT, DATETIME_FORMAT } from "./constants";

/**
 * Format tanggal ISO string menjadi format Indonesia.
 * @param {string|Date} dateStr - Tanggal ISO (contoh: "2026-07-14T09:30:00") atau objek Date
 * @returns {string} Tanggal terformat, contoh: "14 Juli 2026"
 */
export function formatDate(dateStr) {
  if (!dateStr) return "-";
  const d = typeof dateStr === "string" ? parseISO(dateStr) : dateStr;
  return format(d, DATE_FORMAT, { locale: id });
}

/**
 * Format tanggal ISO string menjadi format Indonesia dengan jam.
 * @param {string|Date} dateStr - Tanggal ISO
 * @returns {string} Tanggal + jam terformat, contoh: "14 Jul 2026, 09:30"
 */
export function formatDateTime(dateStr) {
  if (!dateStr) return "-";
  const d = typeof dateStr === "string" ? parseISO(dateStr) : dateStr;
  return format(d, DATETIME_FORMAT, { locale: id });
}

/**
 * Mendapatkan class warna border untuk StatCard berdasarkan status.
 * @param {string} status - Nama status (Available, Borrowed, dll.)
 * @returns {string} CSS class border
 */
export function getStatusBorderColor(status) {
  const map = {
    Available: "border-l-emerald-500",
    Borrowed: "border-l-orange-500",
    Maintenance: "border-l-blue-500",
    Broken: "border-l-red-500",
  };
  return map[status] || "border-l-gray-300";
}

/**
 * Memotong teks ke panjang tertentu dan menambahkan "...".
 * @param {string} text - Teks yang mau dipotong
 * @param {number} max - Panjang maksimal (default 40)
 * @returns {string} Teks terpotong
 */
export function truncateText(text, max = 40) {
  if (!text || text.length <= max) return text;
  return text.slice(0, max) + "...";
}

/**
 * Mendapatkan inisial dari nama lengkap (maks 2 huruf).
 * @param {string} name - Nama lengkap
 * @returns {string} Inisial uppercase
 */
export function getInitials(name) {
  if (!name) return "?";
  const parts = name.trim().split(/\s+/);
  if (parts.length === 1) return parts[0][0].toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}
