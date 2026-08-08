"""Inventory endpoints — CRUD komponen inventaris. (FR-04 s.d FR-14, FR-32 s.d FR-34)"""
from io import BytesIO

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_admin_user, get_current_user_optional
from app.models.user import User
from app.schemas.inventory import (
    ComponentCreate, ComponentUpdate, ItemUpdate,
)
from app.services.inventory_service import InventoryService

router = APIRouter(prefix="/api/v1/inventory", tags=["Inventory"])


# ═══════════ COMPONENTS ═══════════

@router.get("/components")
def list_components(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=200),
    search: str | None = Query(None, description="Cari nama/merek/SN"),
    procurement_year: int | None = Query(None, description="Filter tahun pengadaan"),
    division: str | None = Query(None, description="Filter divisi: Gempa Bumi / Tsunami / Percepatan Tanah"),
    db: Session = Depends(get_db),
):
    service = InventoryService()
    comps, total = service.get_components(db, page=page, size=size, search=search,
                                           procurement_year=procurement_year,
                                           division=division)
    return {
        "status": "success", "message": "Daftar komponen berhasil diambil",
        "data": [c.model_dump() for c in comps],
        "meta": {"page": page, "size": size, "total": total, "total_pages": max(1, (total + size - 1) // size)},
    }


@router.post("/components", status_code=201)
def create_component(
    data: ComponentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    service = InventoryService()
    comp = service.create_component(db, data)
    return {"status": "success", "message": "Komponen berhasil ditambahkan", "data": comp.model_dump()}


# ═══════════ TEMPLATE & IMPORT ═══════════

@router.get("/components/template")
def download_template(
    current_user: User = Depends(get_current_admin_user),
):
    """Download template Excel (.xlsx) untuk import komponen. Admin only."""
    service = InventoryService()
    output = service.generate_template()
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=template_komponen.xlsx"},
    )


@router.post("/components/import")
def import_components(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """Import komponen dari file Excel (.xlsx). Setiap sheet = 1 komponen. Admin only."""
    service = InventoryService()
    result = service.import_from_excel(db, file)
    return result


# ═══════════ COMPONENT BY ID ═══════════

@router.get("/components/{component_id}")
def get_component(
    component_id: int,
    db: Session = Depends(get_db),
):
    service = InventoryService()
    comp = service.get_component(db, component_id)
    return {"status": "success", "message": "Data komponen ditemukan", "data": comp.model_dump()}


@router.put("/components/{component_id}")
def update_component(
    component_id: int,
    data: ComponentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    service = InventoryService()
    comp = service.update_component(db, component_id, data)
    return {"status": "success", "message": "Komponen berhasil diperbarui", "data": comp.model_dump()}


@router.delete("/components/{component_id}")
def delete_component(
    component_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    service = InventoryService()
    return service.delete_component(db, component_id)


# ═══════════ ITEMS (per barang fisik) ═══════════

@router.get("/items")
def list_all_items(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    search: str | None = Query(None, description="Cari serial number"),
    status_id: int | None = Query(None, description="Filter status barang"),
    component_id: int | None = Query(None, description="Filter unit"),
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    """Daftar semua barang individual (lintas unit) dengan filter status, unit, dan search SN.
    Admin dapat melihat barang Dihapuskan, user biasa tidak."""
    service = InventoryService()
    is_admin = current_user is not None and current_user.role.role_name == "Admin"
    items, total = service.get_all_items(
        db, page=page, size=size,
        search=search, status_id=status_id, component_id=component_id,
        include_deleted=is_admin,
    )
    return {
        "status": "success", "message": "Daftar barang berhasil diambil",
        "data": [it.model_dump() for it in items],
        "meta": {"page": page, "size": size, "total": total, "total_pages": max(1, (total + size - 1) // size)},
    }


@router.get("/components/{component_id}/items")
def list_items(
    component_id: int,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    """Daftar item individual dalam satu komponen. Admin dapat melihat barang Dihapuskan."""
    service = InventoryService()
    is_admin = current_user is not None and current_user.role.role_name == "Admin"
    items = service.get_component_items(db, component_id, include_deleted=is_admin)
    return {"status": "success", "message": "Daftar item berhasil diambil", "data": [it.model_dump() for it in items]}


@router.put("/items/{item_id}")
def update_item(
    item_id: int,
    data: ItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """Update item individual (serial number atau status). Admin only. Status hanya bisa diganti antara Available dan Broken."""
    service = InventoryService()
    item = service.update_item(db, item_id, data)
    return {"status": "success", "message": "Item berhasil diperbarui", "data": item.model_dump()}


@router.delete("/items/{item_id}")
def delete_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """Hapus item individual (soft delete). Admin only."""
    service = InventoryService()
    result = service.delete_item(db, item_id)
    return result


@router.get("/items/{item_id}/history")
def get_item_history(
    item_id: int,
    db: Session = Depends(get_db),
):
    """Riwayat perubahan status barang individual."""
    from app.models.item_status_history import ItemStatusHistory
    history = db.query(ItemStatusHistory).filter(
        ItemStatusHistory.inventory_item_id == item_id
    ).order_by(ItemStatusHistory.created_at.desc()).all()

    return {
        "status": "success",
        "message": "Riwayat status berhasil diambil",
        "data": [
            {
                "id": h.id,
                "from_status": h.from_status.status_name if h.from_status else "-",
                "to_status": h.to_status.status_name if h.to_status else "-",
                "source": h.source,
                "notes": h.notes,
                "created_at": h.created_at.isoformat() if h.created_at else None,
                "return_id": h.return_id,
                "borrow_transaction_id": h.borrow_transaction_id,
            }
            for h in history
        ],
    }

