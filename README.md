# Sistem Inventaris Alat Sensor BMKG

Aplikasi inventaris berbasis web untuk mengelola alat sensor di BMKG (Badan Meteorologi, Klimatologi, dan Geofisika). Mencakup pencatatan unit inventaris per barang (serial number), peminjaman dengan verifikasi admin, pengembalian per-SN, perpanjangan masa pinjam, maintenance, export laporan, serta dashboard.

---

## Teknologi

| Layer | Teknologi |
|---|---|
| **Backend** | Python 3.11+, FastAPI, SQLAlchemy ORM, Alembic, JWT |
| **Frontend** | React 18, Vite, Tailwind CSS, TanStack Query |
| **Database** | MySQL 8.0+ |

---

## Struktur Folder

```
Program_Inventaris_Alat/
├── backend/
│   ├── app/
│   │   ├── api/v1/endpoints/    # REST API endpoints
│   │   ├── core/                # Config, database, security, logging, documents
│   │   ├── models/              # SQLAlchemy ORM models
│   │   ├── repositories/        # Data access layer
│   │   ├── schemas/             # Pydantic schemas
│   │   └── services/            # Business logic
│   ├── alembic/                 # Database migrations
│   ├── logs/                    # File log server (app.log, rotasi harian)
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── api/                 # HTTP client (Axios)
│       ├── components/          # UI components
│       ├── contexts/            # AuthContext
│       ├── pages/               # Halaman aplikasi
│       ├── lib/                 # Formatter, constants
│       └── router/              # Routing + proteksi
├── docs/                        # Dokumentasi (requirement, ERD, API, arsitektur)
├── perbaikan/                   # Catatan fitur/perbaikan per tahapan
└── PANDUAN_LOGGER_SERVER.md     # Panduan file log server
```

---

## 1. Setup Database

Buat database MySQL:

```sql
CREATE DATABASE inventaris_bmkg CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
```

Buat file `backend/.env`:

```
DATABASE_URL=mysql+mysqlconnector://root:password@localhost:3306/inventaris_bmkg
SECRET_KEY=bebas-isi-random-string-min-32-karakter
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
DEBUG=true
```

---

## 2. Menjalankan Backend

```bash
cd backend
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend berjalan di **http://localhost:8000** · Swagger UI: **http://localhost:8000/docs**

---

## 3. Menjalankan Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend berjalan di **http://localhost:5173** (proxy ke backend port 8000).

---

## Login Default

| Username | Password | Role |
|---|---|---|
| `admin` | `admin123` | Admin (akses penuh) |

> Ganti password setelah login pertama.

---

## Fitur Utama

| Modul | Fitur |
|---|---|
| **Inventaris** | CRUD unit per barang fisik (serial number), spesifikasi, foto, divisi, bulk import Excel |
| **Petugas** | Data petugas berwenang (NIP, jabatan, instansi) |
| **Peminjam** | Data peminjam internal/eksternal, NIP, email |
| **Peminjaman** | Pilih barang per SN, verifikasi admin (setuju/tolak/batal), dokumen ttd |
| **Perpanjangan** | Ajukan perpanjangan masa pinjam, admin verifikasi (setuju/tolak) |
| **Pengembalian** | Kondisi per-SN (baik/rusak), deteksi keterlambatan + alasan, dokumen ttd, admin verifikasi |
| **Pelimpahan** | Pelimpahan barang ke UPT lain (Draft → Dilimpahkan/Dibatalkan), dokumen ttd |
| **Maintenance** | Catat perbaikan per barang, update status komponen otomatis |
| **Nomor Transaksi** | Nomor unik format `YYYYMMDDNNN` + nomor urut harian (reset per hari) |
| **Arsip Transaksi** | Snapshot otomatis transaksi selesai ke tabel JSON — riwayat tidak berubah walau data master berubah |
| **Soft Delete** | Peminjam/petugas/unit bisa dihapus walau punya riwayat transaksi selesai |
| **Dashboard** | Statistik inventaris, pie chart |
| **Export** | PDF & Excel laporan |
| **Log Aktivitas** | Audit trail seluruh aksi pengguna (admin only) + link ke transaksi terkait |
| **Log Server** | File log `backend/logs/app.log` — rotasi harian, retensi 30 hari, error + traceback otomatis |

---

## Nomor Transaksi

Setiap transaksi peminjaman & pengembalian mendapat **2 nomor**:

| Kolom | Penjelasan | Contoh |
|---|---|---|
| **No.** | Nomor urut harian, reset setiap hari | `1`, `2`, `3`, ... |
| **No. Transaksi** | Nomor unik permanen format TahunBulanTanggalNomor | `20260826001` |

---

## File Log Server

- Lokasi: `backend/logs/app.log` — **otomatis dibuat** saat backend dijalankan.
- Rotasi harian + retensi 30 hari, output juga tampil di konsol.
- Mencatat: login, operasi transaksi penting (buat/setujui/tolak/verifikasi/hapus/import), dan error 500 + traceback otomatis.
- Panduan lengkap: **`PANDUAN_LOGGER_SERVER.md`** (di root proyek).

---

## Perbedaan Role

| Aksi | Admin | User |
|---|---|---|
| Lihat inventaris & transaksi | ✅ | ✅ |
| Buat peminjaman | ✅ | ✅ |
| Ajukan perpanjangan | ✅ | ✅ |
| Setujui/tolak peminjaman | ✅ | ❌ |
| Proses pengembalian | ✅ | ❌ |
| Verifikasi pengembalian | ✅ | ❌ |
| Catat maintenance | ✅ | ❌ |
| Kelola petugas & peminjam | ✅ | ❌ |
| Buat pelimpahan ke UPT | ✅ | ❌ |
| Kelola pengguna | ✅ | ❌ |
| Lihat log aktivitas | ✅ | ❌ |

---

## Catatan

- Identifier kode dalam Bahasa Inggris, komentar domain logic dalam Bahasa Indonesia.
- Nama folder parent `Proyek_Investaris_Alat` vs project `Program_Inventaris_Alat` — inkonsistensi existing, jangan direname.
- Riwayat perubahan/penambahan fitur terdokumentasi di folder `perbaikan/` (satu file .md per tahapan).
- `backend/logs/` sudah di-ignore oleh Git (file log tidak ikut di-commit).
