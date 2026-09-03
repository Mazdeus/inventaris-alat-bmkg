# Sistem Inventaris Alat BMKG

Aplikasi inventaris berbasis web untuk mengelola alat di BMKG (Badan Meteorologi, Klimatologi, dan Geofisika). Mencakup pencatatan unit inventaris per barang fisik (*serial number*), peminjaman dengan persetujuan admin, pengembalian kondisi per-SN, pelimpahan antar-UPT, pemeliharaan (*maintenance*), kompresi otomatis foto/dokumen, pencatatan riwayat status barang, ekspor laporan BAST resmi (PDF/Excel), pengingat email otomatis jatuh tempo (H-2 & Overdue) untuk Admin, serta audit log aktivitas.

---

## Teknologi

| Layer | Teknologi |
|---|---|
| **Backend** | Python 3.11+, FastAPI, SQLAlchemy ORM, Alembic, APScheduler, aiosmtplib, Pillow, FPDF2, JWT |
| **Frontend** | React 18, Vite, Tailwind CSS, TanStack Query, Lucide Icons, HTML5 Canvas |
| **Database** | MySQL 8.0+ |

---

## Struktur Folder

```
Program_Inventaris_Alat/
├── backend/
│   ├── app/
│   │   ├── api/v1/endpoints/    # REST API endpoints
│   │   ├── core/                # Config, database, security, logging, mail, scheduler, upload
│   │   ├── models/              # SQLAlchemy ORM models
│   │   ├── repositories/        # Data access layer
│   │   ├── schemas/             # Pydantic schemas
│   │   ├── services/            # Business logic (reminder_service, dll)
│   │   └── templates/emails/    # Template email HTML resmi BMKG
│   ├── alembic/                 # Database migrations
│   ├── logs/                    # File log server (app.log, rotasi harian)
│   ├── uploads/                 # Direktori penyimpanan file upload (foto, BAST)
│   ├── .env.example             # Template file konfigurasi environment backend
│   ├── clear_data.py            # Skrip reset database & pembersihan file upload
│   ├── seed.py                  # Seeder data awal (roles, status master, admin)
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── api/                 # HTTP client (Axios)
│       ├── components/          # UI components (EmailControlModal, ItemStatusTimeline, dll)
│       ├── contexts/            # AuthContext
│       ├── pages/               # Halaman aplikasi (Dashboard, Peminjaman, dll)
│       ├── lib/                 # Formatter, constants, imageCompressor
│       └── router/              # Routing + proteksi auth
├── docs/                        # Dokumentasi (requirement, ERD, API, arsitektur)
├── perbaikan/                   # Catatan fitur/perbaikan per tahapan
└── PANDUAN_LOGGER_SERVER.md     # Panduan file log server
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

6. Jalankan seeder untuk memasukkan data master awal (Roles, Master Status, Akun Admin Default):
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

> Disarankan untuk memperbarui email admin di menu Pengguna (misal ke `fadhilcr1@gmail.com`) agar dapat menerima notifikasi peringatan peminjaman.

---

## Fitur Utama Sistem

| Modul | Fitur |
|---|---|
| **Inventaris** | CRUD unit inventaris per barang fisik (*serial number*), spesifikasi, foto, divisi, bulk import Excel |
| **Petugas** | Data petugas berwenang (NIP, nama, jabatan, instansi) |
| **Peminjam** | Data peminjam internal/eksternal, NIP, kontak, instansi |
| **Peminjaman** | Pengajuan barang per-SN, persetujuan admin (setujui/tolak/batal), cetak BAST PDF resmi BMKG |
| **Perpanjangan** | Pengajuan perpanjangan masa pinjam, verifikasi admin (setuju/tolak) |
| **Pengembalian** | Pengecekan kondisi per-SN (baik/rusak), hitung denda/keterlambatan, verifikasi admin, cetak BAST PDF |
| **Pelimpahan** | Pelimpahan alat antar-UPT BMKG (Draft → Dilimpahkan), cetak BAST PDF Pelimpahan resmi |
| **Pemeliharaan** | Catat perbaikan barang (*maintenance*), update otomatis ketersediaan unit |
| **Email Alert & Pengingat** | Notifikasi otomatis via email (H-2 sebelum tenggat, Hari-H, & Overdue) ke Admin BMKG dengan rincian Serial Number, cron scheduler background, serta modal kontrol & tes SMTP |
| **Riwayat Status Barang** | Tracking lengkap linimasa status fisik barang (*Available, Ditahan, Borrowed, Maintenance, Broken, Dilimpahkan*) lengkap dengan tombol referensi langsung ke transaksi |
| **Kompresi Upload Otomatis** | Dual-layer kompresi (HTML5 Canvas di browser + Pillow di server) untuk foto & scan dokumen hingga 90% lebih hemat storage |
| **Nomor Transaksi Resmi** | Format unik `PJ-YYYYMMDDNNN` (Peminjaman), `KB-YYYYMMDDNNN` (Pengembalian), dll + nomor urut harian |
| **Snapshot Arsip Transaksi** | Snapshot otomatis transaksi selesai ke arsip JSON — data laporan historis tidak berubah walau data master disunting/dihapus |
| **Reset Data (`clear_data.py`)** | Skrip pembersihan seluruh 22 tabel data transaksi & inventaris, reset auto-increment ke 1, serta membersihkan file upload fisik |
| **Dashboard** | Statistik total inventaris, status distribusi, ringkasan peminjaman & pemeliharaan |
| **Log Aktivitas & Server** | Audit trail aksi pengguna serta file log `backend/logs/app.log` dengan rotasi harian |


---

## Skrip Utilitas Tambahan

* **Reset Data Uji Coba**:
  ```bash
  cd backend
  python clear_data.py
  ```
  *Membersihkan seluruh transaksi dan file upload uji coba, mengembalikan sistem ke kondisi awal (hanya menyisakan akun admin dan data master).*

---

## Catatan Tambahan

- Identifier kode dan nama fungsi ditulis dalam **Bahasa Inggris**, komentar logika domain dan tampilan antarmuka dalam **Bahasa Indonesia**.
- Nama folder parent `Proyek_Investaris_Alat` vs direktori proyek `Program_Inventaris_Alat` dipertahankan sesuai struktur awal repositori.
- File log server di `backend/logs/` dan file `.env` diabaikan oleh Git (*git ignored*).

