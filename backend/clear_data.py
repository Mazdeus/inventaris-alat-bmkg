"""Clear semua data transaksi & inventaris, hanya simpan data master (roles, statuses, akun admin)."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
os.chdir(os.path.dirname(__file__))

from sqlalchemy import text
from app.core.database import SessionLocal
from app.models.borrow_detail import BorrowDetail
from app.models.borrow_detail_item import BorrowDetailItem
from app.models.borrow_extension import BorrowExtension
from app.models.borrow_transaction import BorrowTransaction
from app.models.borrower import Borrower
from app.models.handover import Handover
from app.models.handover_item import HandoverItem
from app.models.inventory_component import InventoryComponent
from app.models.inventory_item import InventoryItem
from app.models.item_status_history import ItemStatusHistory
from app.models.maintenance import Maintenance
from app.models.maintenance_item import MaintenanceItem
from app.models.officer import Officer
from app.models.return_ import Return
from app.models.return_detail import ReturnDetail
from app.models.return_detail_item import ReturnDetailItem
from app.models.activity_log import ActivityLog
from app.models.email_notification_log import EmailNotificationLog
from app.models.refresh_token import RefreshToken
from app.models.transaction_counter import TransactionCounter
from app.models.transaction_snapshot import TransactionSnapshot
from app.models.upt import Upt
from app.models.user import User

db = SessionLocal()

keep_users = ["admin"]

try:
    # ⚠️ Hapus dari child ke parent (hindari FK constraint error)
    tables = [
        # Log notifikasi email (child dari borrow_transactions & users)
        ("email_notification_logs", EmailNotificationLog),
        # Pelimpahan
        ("handover_items", HandoverItem),
        ("handovers", Handover),
        # Pengembalian — detail items sebelum details
        ("return_detail_items", ReturnDetailItem),
        ("return_details", ReturnDetail),
        ("returns", Return),
        # Peminjaman — detail items, perpanjangan sebelum details
        ("borrow_detail_items", BorrowDetailItem),
        ("borrow_extensions", BorrowExtension),
        ("borrow_details", BorrowDetail),
        ("borrow_transactions", BorrowTransaction),
        # Maintenance & Log — junction dulu sebelum parent
        ("maintenance_items", MaintenanceItem),
        ("maintenance", Maintenance),
        ("activity_logs", ActivityLog),
        # Snapshot transaksi selesai (arsip JSON — FK ke users SET NULL)
        ("transaction_snapshots", TransactionSnapshot),
        # Inventaris — items sebelum komponen, history sebelum items
        ("item_status_history", ItemStatusHistory),
        ("inventory_items", InventoryItem),
        ("inventory_components", InventoryComponent),
        # Peminjam
        ("borrowers", Borrower),
        # Petugas
        ("officers", Officer),
        # UPT
        ("upts", Upt),
        # Counter nomor transaksi harian (reset agar nomor mulai dari 001 lagi)
        ("transaction_counters", TransactionCounter),
        # Refresh tokens (sebelum users)
        ("refresh_tokens", RefreshToken),
    ]

    # ⚠️ Tabel yang TIDAK dihapus (data master):
    #   - users             (akan dihapus kecuali admin — lihat bawah)
    #   - roles             (master: Admin)
    #   - inventory_status  (master: Available, Ditahan, Borrowed, Maintenance, Broken, Dihapuskan, Dilimpahkan)
    #
    # Tabel baru yang IKUT dihapus/direset:
    #   - transaction_snapshots  (arsip transaksi selesai — dihapus agar bersih)
    #   - transaction_counters   (counter nomor transaksi — direset agar nomor mulai dari 001 lagi)
    #
    # Catatan: kolom procurement_month pada inventory_components TIDAK terpengaruh
    # oleh clear data — script hanya menghapus baris, bukan struktur tabel.

    total = 0
    for name, model in tables:
        count = db.query(model).count()
        if count > 0:
            db.query(model).delete()
            db.commit()  # commit delete dulu sebelum reset AUTO_INCREMENT
            # Reset AUTO_INCREMENT — pakai TRUNCATE-style reset yang lebih agresif
            db.execute(text(f"ALTER TABLE {name} AUTO_INCREMENT = 1"))
            db.commit()
            total += count
            print(f"  [OK] {name}: {count} data dihapus, AUTO_INCREMENT reset ke 1")
        else:
            print(f"  [--] {name}: kosong")

    # Hapus user kecuali admin
    users_deleted = db.query(User).filter(~User.username.in_(keep_users)).delete(synchronize_session=False)
    if users_deleted:
        db.commit()
        print(f"  [OK] users (kecuali {', '.join(keep_users)}): {users_deleted} dihapus")

    # Bersihkan file fisik yang tersimpan di folder uploads/
    from pathlib import Path
    upload_dir = Path("uploads")
    deleted_files_count = 0
    if upload_dir.exists():
        for file_path in upload_dir.rglob("*"):
            if file_path.is_file() and not file_path.name.startswith("."):
                try:
                    file_path.unlink()
                    deleted_files_count += 1
                except Exception:
                    pass
    if deleted_files_count > 0:
        print(f"  [OK] uploads: {deleted_files_count} file fisik lampiran/foto dibersihkan")
    else:
        print(f"  [--] uploads: direktori file fisik sudah bersih")

    db.commit()
    print(f"\n  Total {total + users_deleted} baris data tabel & {deleted_files_count} file fisik dibersihkan.")
    print(f"  Data yang dipertahankan:")
    print(f"    - Akun: {', '.join(keep_users)}")
    print(f"    - Role (Admin, User) — tidak dihapus")
    print(f"    - Status inventaris (Available, Ditahan, Borrowed, Maintenance, Broken, Dihapuskan, Dilimpahkan) — tidak dihapus")
    print(f"  Catatan: snapshot transaksi & counter nomor transaksi ikut direset.")

except Exception as e:
    db.rollback()
    print(f"  [ERROR] {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()

