# Sistem Inventaris Alat BMKG (Versi 1.0)

Aplikasi manajemen inventaris berbasis web untuk mengelola peralatan operasional di BMKG (Badan Meteorologi, Klimatologi, dan Geofisika). Mencakup pencatatan unit inventaris per barang fisik (*serial number*), peminjaman dengan persetujuan admin, pengembalian kondisi per-SN, pelimpahan antar-UPT BMKG se-Indonesia, pemeliharaan (*maintenance*), kompresi otomatis foto/dokumen, pencatatan riwayat status barang, ekspor laporan BAST resmi (PDF/Excel), pengingat email otomatis jatuh tempo (H-2 & Overdue) untuk Admin, audit log aktivitas dengan pencarian cerdas, serta indikator loading modern.

---

## Teknologi

| Layer | Teknologi |
|---|---|
| **Backend** | Python 3.11+, FastAPI, SQLAlchemy ORM, Alembic, APScheduler, aiosmtplib, Pillow, FPDF2, JWT, MySQL Connector |
| **Frontend** | React 18, Vite, Tailwind CSS, TanStack Query v5, Lucide Icons, Sonner Toast, HTML5 Canvas, Axios |
| **Database** | MySQL 8.0+ |

---

## Struktur Folder

```
Program_Inventaris_Alat/
├── backend/
│   ├── app/
│   │   ├── api/v1/endpoints/    # REST API endpoints (borrow, returns, handovers, upts, dll)
│   │   ├── core/                # Config, database, security, logging, mail, scheduler, upload, documents
│   │   ├── models/              # SQLAlchemy ORM models (upt, handover, borrow, maintenance, dll)
│   │   ├── repositories/        # Data access layer
│   │   ├── schemas/             # Pydantic validation schemas (DTO)
│   │   ├── services/            # Business logic (reminder_service, upt_service, dll)
│   │   └── templates/emails/    # Template email HTML resmi BMKG
│   ├── alembic/                 # Skrip migrasi database
│   ├── logs/                    # File log server (app.log, rotasi harian)
│   ├── uploads/                 # Direktori penyimpanan file upload fisik (foto, scan BAST)
│   ├── .env.example             # Template file konfigurasi environment backend
│   ├── clear_data.py            # Skrip reset database & pembersihan file upload
│   ├── seed.py                  # Seeder data awal (roles, master status, admin default)
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── api/                 # HTTP client (Axios endpoints)
│       ├── components/          # Reusable UI components (DataTable, StatCard, DatePresetFilter, dll)
│       ├── contexts/            # AuthContext & Session management
│       ├── pages/               # Halaman aplikasi (Dashboard, Peminjaman, UPT, Activity Logs, dll)
│       ├── lib/                 # Formatter, constants, imageCompressor
│       └── router/              # Routing SPA + proteksi autentikasi
└── README.md
```

---

## Panduan Instalasi & Menjalankan Aplikasi

### 1. Setup Database MySQL

1. Pastikan layanan MySQL server telah aktif (misal via XAMPP / MySQL Service).
2. Buat database baru:
   ```sql
   CREATE DATABASE inventaris_bmkg CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
   ```

---

### 2. Setup & Konfigurasi Backend

1. Buka terminal dan masuk ke folder `backend`:
   ```bash
   cd backend
   ```

2. Buat file konfigurasi `.env` dari template:
   ```bash
   cp .env.example .env
   # Atau di Windows PowerShell:
   # copy .env.example .env
   ```

3. Sesuaikan isi file `backend/.env` sesuai konfigurasi lokal Anda:
   ```env
   # Koneksi Database MySQL (format: mysql+mysqlconnector://user:password@host:port/database)
   DATABASE_URL=mysql+mysqlconnector://root:password@localhost:3306/inventaris_bmkg

   # Secret Key JWT (string acak minimal 32 karakter)
   SECRET_KEY=ganti_dengan_random_string_aman_minimal_32_karakter_contoh_d83fa9012bcfe87
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=60

   # Mode Debug
   DEBUG=true

   # URL Basis Backend (untuk akses aset upload)
   BASE_URL=http://localhost:8000

   # Konfigurasi SMTP Email (Gmail App Password - 100% Gratis)
   SMTP_ENABLED=true
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USER=email_pengirim@gmail.com
   SMTP_PASSWORD=ganti_dengan_16_digit_google_app_password
   SMTP_FROM_EMAIL=email_pengirim@gmail.com
   SMTP_FROM_NAME="Sistem Inventaris BMKG"
   SMTP_TLS=true
   SMTP_SSL=false

   # Waktu Eksekusi Pengecekan Cron Otomatis Harian (Jam 08:00 WIB)
   EMAIL_REMINDER_CRON_HOUR=8
   EMAIL_REMINDER_CRON_MINUTE=0
   ```

4. Install dependensi Python:
   ```bash
   pip install -r requirements.txt
   ```

5. Jalankan migrasi database:
   ```bash
   alembic upgrade head
   ```

6. Jalankan seeder untuk memasukkan data master awal (Roles, Master Status, Akun Admin Default, dan UPT):
   ```bash
   python seed.py
   ```

7. Jalankan server backend:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

* Backend berjalan di: **http://localhost:8000**
* Dokumentasi Interaktif Swagger UI: **http://localhost:8000/docs**

---

### 3. Setup & Menjalankan Frontend

1. Buka terminal baru dan masuk ke folder `frontend`:
   ```bash
   cd frontend
   ```

2. Install dependensi Node.js:
   ```bash
   npm install
   ```

3. Jalankan server development frontend:
   ```bash
   npm run dev
   ```

* Frontend berjalan di: **http://localhost:5173**

---

## Akun Login Default

Setelah menjalankan `python seed.py`, gunakan akun default berikut:

| Username | Password | Role | Keterangan |
|---|---|---|---|
| `admin` | `admin123` | Admin | Akses penuh seluruh sistem |

> Disarankan untuk memperbarui email admin di menu Pengguna agar dapat menerima notifikasi email peringatan peminjaman secara otomatis.

---

## Fitur Utama Sistem (Versi 1.0)

| Modul | Fitur & Deskripsi |
|---|---|
| **Dasbor Interaktif** | Ringkasan stok fisik alat, statistik peminjaman aktif & terlambat, filter tahun dinamis tepat di atas tren transaksi, serta grafik aktivitas bulanan. |
| **Unit Inventaris** | Manajemen alat fisik per-Serial Number (SN), foto alat, spesifikasi teknis, merek, model, serta fitur **Bulk Import Excel** multi-sheet. |
| **Peminjaman** | Formulir peminjaman unit dengan pemilihan Serial Number fisik yang tersedia (status *Ditahan*), persetujuan Admin (Setujui/Tolak/Batalkan), pengunggahan dokumen bertandatangan, serta cetak BAST PDF resmi BMKG. |
| **Perpanjangan Masa Pinjam** | Pengajuan tanggal tenggat baru dan alasan perpanjangan oleh peminjam/staf, verifikasi persetujuan/penolakan oleh Admin, serta update otomatis jadwal pengembalian. |
| **Pengembalian** | Pengecekan kondisi fisik per-SN (Baik/Rusak/Hilang), kalkulasi keterlambatan/denda, verifikasi admin, update otomatis ketersediaan stok, dan cetak BAST Pengembalian. |
| **Pelimpahan Antar-UPT** | Pelimpahan alat ke Unit Pelaksana Teknis (UPT) BMKG se-Indonesia. Kolom *UPT Penerima* terintegrasi dengan pencarian autocomplete, pencatatan *Nama Penerima* & *NIP Penerima*, status BMN (*BMN Tercatat/Belum Tercatat*), serta cetak BAST Pelimpahan resmi. |
| **Master Data UPT** | Modul data kantor/stasiun UPT BMKG (191 stasiun se-Indonesia) mencakup nama, alamat, kontak, status aktif, pencarian, dan proteksi hapus dengan konfirmasi password admin. |
| **Pemeliharaan (*Maintenance*)** | Pencatatan servis dan perbaikan alat per-SN, status pengerjaan (*Pending, In Progress, Completed*), serta pengembalian status unit ke *Available* setelah selesai. |
| **Petugas & Peminjam** | Master data petugas verifikator BMKG dan peminjam internal/eksternal (NIP, kontak, instansi, jabatan). |
| **Email Alert Otomatis** | Pengingat email otomatis (H-2 tenggat waktu, Hari-H, dan *Overdue*) dengan rincian Serial Number alat, scheduler cron harian, serta tombol kirim alert manual. |
| **Audit Log & Pencarian Cerdas** | Riwayat aktivitas sistem yang dapat dicari berdasarkan kata kunci tindakan (*peminjaman, pelimpahan, dll*) maupun nama staf/admin, terintegrasi debouncing 300ms. |
| **Indikator Loading Modern** | Search bar dengan animasi spinner (`Loader2`) & teks status, progress bar dinamis (*indeterminate bar*), serta *smooth table dimming* yang mencegah layar berkedip putih saat mencari data. |
| **Navigasi & Pagination Lengkap** | Fitur lompat halaman langsung (*Ke hal: [input]*), filter rentang tanggal cepat (*"Pilih Tanggal"*), serta tombol navigasi instan antar transaksi terkait. |
| **Kompresi Upload Otomatis** | Kompresi ganda (Canvas HTML5 di browser + Pillow di server) mereduksi ukuran foto dan scan dokumen hingga 90% lebih hemat penyimpanan. |
| **Snapshot Arsip Transaksi** | Penyimpanan snapshot arsip JSON transaksi selesai sehingga laporan riwayat historis tetap valid walau data master alat mengalami perubahan di masa depan. |

---

## Catatan Konvensi

- Identifier kode, nama variabel, dan fungsi ditulis dalam **Bahasa Inggris** mengikuti best practices.
- Komentar logika domain, dokumentasi, label antarmuka pengguna, dan pesan notifikasi disajikan dalam **Bahasa Indonesia** standar BMKG.
