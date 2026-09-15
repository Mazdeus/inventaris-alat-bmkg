"""
Seeder script — mengisi data awal ke database inventaris_bmkg.
Jalankan: python seed.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.role import Role
from app.models.user import User
from app.models.inventory_status import InventoryStatus


def seed_roles(db):
    """Insert default roles: Admin only."""
    roles_data = [
        {"id": 1, "role_name": "Admin"},
    ]
    for data in roles_data:
        existing = db.query(Role).filter(Role.id == data["id"]).first()
        if not existing:
            db.add(Role(**data))
            print(f"  + Role: {data['role_name']}")
        else:
            print(f"  = Role: {data['role_name']} (already exists)")
    db.commit()


def seed_inventory_statuses(db):
    """Insert default inventory statuses."""
    statuses_data = [
        {"id": 1, "status_name": "Available"},
        {"id": 2, "status_name": "Borrowed"},
        {"id": 3, "status_name": "Maintenance"},
        {"id": 4, "status_name": "Broken"},
        {"id": 5, "status_name": "Deleted"},
        {"id": 6, "status_name": "Transferred"},
        {"id": 7, "status_name": "On Hold"},
    ]
    for data in statuses_data:
        existing = db.query(InventoryStatus).filter(InventoryStatus.id == data["id"]).first()
        if not existing:
            db.add(InventoryStatus(**data))
            print(f"  + Status: {data['status_name']}")
        else:
            print(f"  = Status: {data['status_name']} (already exists)")
    db.commit()


def seed_admin_user(db):
    """Insert default admin user — username: admin, password: admin123."""
    existing = db.query(User).filter(User.username == "admin").first()
    if not existing:
        admin = User(
            role_id=1,
            username="admin",
            password=hash_password("admin123"),
            full_name="Administrator",
            is_active=True,
        )
        db.add(admin)
        db.commit()
        print(f"  + User: admin (password: admin123)")
    else:
        print(f"  = User: admin (already exists)")


from app.models.upt import Upt


def seed_upts(db):
    """Insert seluruh 191 UPT BMKG se-Indonesia dari file bmkg_upts.json.
    Jika file tidak ada, fallback memasukkan 3 sample UPT."""
    import json
    import os

    json_path = os.path.join(os.path.dirname(__file__), "bmkg_upts.json")
    if os.path.exists(json_path):
        with open(json_path, "r", encoding="utf-8") as f:
            upts_data = json.load(f)
        for data in upts_data:
            existing = db.query(Upt).filter(Upt.name == data["name"]).first()
            if not existing:
                db.add(Upt(
                    name=data["name"][:150],
                    address=data.get("address"),
                    phone=data.get("phone")[:50] if data.get("phone") else None,
                ))
        db.commit()
        total_upts = db.query(Upt).filter(Upt.deleted_at.is_(None)).count()
        print(f"  + Seeded {total_upts} UPTs from bmkg_upts.json")
        return

    sample_upts = [
        {
            "name": "Stasiun Geofisika Bandung",
            "address": "Jl. Cemara No. 66, Pasteur, Kec. Sukajadi, Kota Bandung, Jawa Barat 40161",
            "phone": "(022) 2038794",
        },
        {
            "name": "Balai Besar MKG Wilayah II Tangerang Selatan",
            "address": "Jl. Meteorologi No. 5, Pondok Betung, Pondok Aren, Tangerang Selatan, Banten 15221",
            "phone": "(021) 73691621",
        },
        {
            "name": "Stasiun Klimatologi Jawa Barat",
            "address": "Jl. Raya Dramaga KM 8, Babakan, Kec. Dramaga, Kabupaten Bogor, Jawa Barat 16680",
            "phone": "(0251) 8622144",
        },
    ]
    for data in sample_upts:
        existing = db.query(Upt).filter(Upt.name == data["name"]).first()
        if not existing:
            db.add(Upt(**data))
            print(f"  + UPT: {data['name']}")
        else:
            print(f"  = UPT: {data['name']} (already exists)")
    db.commit()


def main():
    db = SessionLocal()
    try:
        print("Seeding roles...")
        seed_roles(db)

        print("Seeding inventory statuses...")
        seed_inventory_statuses(db)

        print("Seeding admin user...")
        seed_admin_user(db)

        print("Seeding UPTs...")
        seed_upts(db)

        print("\nSeeder completed successfully!")
    except Exception as e:
        db.rollback()
        print(f"\nSeeder failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()