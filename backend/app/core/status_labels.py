"""Label Bahasa Indonesia untuk nilai status internal (English).

Dipakai untuk menerjemahkan nilai status (yang disimpan dalam Bahasa Inggris di
database) menjadi label Indonesia saat ditampilkan dalam pesan error / respons.
Tampilan browser tetap Bahasa Indonesia.
"""

# Mapping nilai internal (English) → label tampilan (Indonesia)
STATUS_LABELS_ID = {
    "Pending": "Menunggu",
    "Borrowed": "Dipinjam",
    "Returned": "Dikembalikan",
    "Cancelled": "Dibatalkan",
    "Completed": "Selesai",
    "Approved": "Disetujui",
    "Rejected": "Ditolak",
    "Transferred": "Dilimpahkan",
    "On Hold": "Ditahan",
    "Deleted": "Dihapuskan",
    "Maintenance": "Perbaikan",
    "Broken": "Rusak",
    "Available": "Tersedia",
    "Good": "Baik",
    "Damaged": "Rusak",
    "Draft": "Draft",
    "In Progress": "Dalam Proses",
    "Internal": "Internal",
    "External": "Eksternal",
}


def status_label(value: str | None) -> str:
    """Kembalikan label Indonesia untuk nilai status; fallback ke nilai asli."""
    if value is None:
        return "-"
    return STATUS_LABELS_ID.get(value, value)
