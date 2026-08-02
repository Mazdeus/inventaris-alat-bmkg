"""InventoryService — logika bisnis untuk komponen inventaris."""
from io import BytesIO

from fastapi import HTTPException, UploadFile
from openpyxl import Workbook, load_workbook
from sqlalchemy.orm import Session

from app.models.inventory_component import InventoryComponent
from app.models.inventory_item import InventoryItem
from app.repositories.inventory_component_repository import InventoryComponentRepository
from app.schemas.inventory import (
    ComponentBrief, ComponentCreate, ComponentResponse, ComponentUpdate,
    ItemResponse, ItemUpdate,
)


class InventoryService:
    def __init__(self):
        self.comp_repo = InventoryComponentRepository()

    # ── Component ──

    def _comp_response(self, comp: InventoryComponent) -> ComponentResponse:
        available = self.comp_repo.get_available_quantity(db=None, component_id=comp.id) if hasattr(self, '_db') else 0
        return ComponentResponse(
            id=comp.id, item_name=comp.item_name, brand=comp.brand, model=comp.model,
            serial_number=comp.serial_number, procurement_year=comp.procurement_year,
            supplier=comp.supplier, total_quantity=comp.total_quantity,
            specifications=comp.specifications or "",
            photo_url=comp.photo_url, photo_path=comp.photo_path,
            division=comp.division or "",
            available_quantity=available,
            status=comp.status.status_name if comp.status else "",
            notes=comp.notes,
        )

    def _comp_response_with_db(self, db: Session, comp: InventoryComponent) -> ComponentResponse:
        available = self.comp_repo.get_available_quantity(db, comp.id)
        items_list = db.query(InventoryItem).filter(
            InventoryItem.inventory_component_id == comp.id
        ).all()
        derived_status = self._derive_status_from_items(items_list, comp)
        return ComponentResponse(
            id=comp.id, item_name=comp.item_name, brand=comp.brand, model=comp.model,
            serial_number=comp.serial_number, procurement_year=comp.procurement_year,
            supplier=comp.supplier, total_quantity=comp.total_quantity,
            specifications=comp.specifications or "",
            photo_url=comp.photo_url, photo_path=comp.photo_path,
            division=comp.division or "",
            available_quantity=available,
            status=derived_status,
            notes=comp.notes,
            items=[ItemResponse(
                id=it.id, inventory_component_id=it.inventory_component_id,
                serial_number=it.serial_number,
                status=it.status.status_name if it.status else "",
                notes=it.notes,
            ) for it in items_list],
        )

    def _derive_status_from_items(self, items: list, comp) -> str:
        """Hitung status komponen dari item-itemnya. Prioritas: Available > Borrowed > Maintenance > Broken."""
        if not items:
            return comp.status.status_name if comp.status else "Available"
        status_names = [it.status.status_name for it in items]
        if "Available" in status_names:
            return "Available"
        if "Borrowed" in status_names:
            return "Borrowed"
        if "Maintenance" in status_names:
            return "Maintenance"
        if "Broken" in status_names:
            return "Broken"
        return status_names[0] if status_names else "Available"

    def get_components(
        self, db: Session, *, page: int = 1, size: int = 10,
        search: str | None = None, status_id: int | None = None,
        procurement_year: int | None = None, division: str | None = None,
    ):
        skip = (page - 1) * size
        comps = self.comp_repo.search_components(
            db, search=search, status_id=status_id,
            procurement_year=procurement_year, division=division, skip=skip, limit=size,
        )
        total = self.comp_repo.count_filtered(
            db, search=search, status_id=status_id,
            procurement_year=procurement_year, division=division,
        )
        return [self._comp_response_with_db(db, c) for c in comps], total

    def get_component(self, db: Session, component_id: int) -> ComponentResponse:
        comp = self.comp_repo.get(db, component_id)
        if not comp:
            raise HTTPException(status_code=404, detail="Unit tidak ditemukan")
        return self._comp_response_with_db(db, comp)

    def create_component(self, db: Session, data: ComponentCreate) -> ComponentResponse:
        comp_data = data.model_dump()
        comp_data.pop("serial_numbers", None)
        comp_data["status_id"] = 1  # default: Available
        comp = self.comp_repo.create(db, comp_data)

        # Validasi: setiap barang wajib punya serial number
        for i in range(data.total_quantity):
            sn = None
            if data.serial_numbers and i < len(data.serial_numbers):
                sn = data.serial_numbers[i] if data.serial_numbers[i] else None
            if not sn:
                raise HTTPException(
                    status_code=400,
                    detail=f"Serial Number untuk barang ke-{i + 1} wajib diisi"
                )
            db.add(InventoryItem(
                inventory_component_id=comp.id,
                serial_number=sn,
                status_id=1,  # Available
            ))
        db.commit()
        db.refresh(comp)

        return self._comp_response_with_db(db, comp)

    def update_component(self, db: Session, component_id: int, data: ComponentUpdate) -> ComponentResponse:
        comp = self.comp_repo.get(db, component_id)
        if not comp:
            raise HTTPException(status_code=404, detail="Unit tidak ditemukan")

        old_quantity = comp.total_quantity
        new_quantity = data.total_quantity if data.total_quantity is not None else old_quantity

        # Update komponen (exclude serial_numbers dari data mentah, urus manual)
        update_data = data.model_dump(exclude_unset=True)
        serial_nums = update_data.pop("serial_numbers", None) or []

        comp = self.comp_repo.update(db, comp, update_data)

        # ── Sinkronisasi inventory_items ──

        # Jika quantity bertambah → buat item baru (wajib isi SN)
        if new_quantity > old_quantity:
            diff = new_quantity - old_quantity
            for i in range(diff):
                sn = None
                # Ambil SN dari index old_quantity ke atas (SN untuk barang baru)
                sn_idx = old_quantity + i
                if serial_nums and sn_idx < len(serial_nums):
                    sn = serial_nums[sn_idx] if serial_nums[sn_idx] else None
                if not sn:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Serial Number untuk barang baru ke-{i + 1} wajib diisi"
                    )
                db.add(InventoryItem(
                    inventory_component_id=comp.id,
                    serial_number=sn,
                    status_id=1,  # Available
                ))

        # Jika quantity berkurang → hapus item berlebih (hanya yang Available)
        if new_quantity < old_quantity:
            diff = old_quantity - new_quantity
            items_to_delete = (
                db.query(InventoryItem)
                .filter(
                    InventoryItem.inventory_component_id == comp.id,
                    InventoryItem.status_id == 1,  # Available only
                )
                .order_by(InventoryItem.id.desc())
                .limit(diff)
                .all()
            )
            if len(items_to_delete) < diff:
                raise HTTPException(
                    status_code=400,
                    detail=f"Tidak bisa mengurangi quantity — hanya {len(items_to_delete)} barang tersedia (sisanya sedang dipinjam/diperbaiki)"
                )
            for item in items_to_delete:
                db.delete(item)

        db.commit()
        db.refresh(comp)
        return self._comp_response_with_db(db, comp)

    def delete_component(self, db: Session, component_id: int) -> dict:
        comp = self.comp_repo.get(db, component_id)
        if not comp:
            raise HTTPException(status_code=404, detail="Unit tidak ditemukan")
        if self.comp_repo.is_being_borrowed(db, component_id):
            raise HTTPException(status_code=409, detail="Unit tidak bisa dihapus — sedang dipinjam")
        if hasattr(comp, 'items') and comp.items:
            for item in comp.items:
                db.delete(item)
        self.comp_repo.delete(db, component_id)
        return {"status": "success", "message": f"Unit '{comp.item_name}' berhasil dihapus"}

    # ── Item (per barang fisik) ──

    def get_component_items(self, db: Session, component_id: int) -> list[ItemResponse]:
        comp = self.comp_repo.get(db, component_id)
        if not comp:
            raise HTTPException(status_code=404, detail="Unit tidak ditemukan")
        items = db.query(InventoryItem).filter(
            InventoryItem.inventory_component_id == component_id
        ).all()
        return [ItemResponse(
            id=it.id, inventory_component_id=it.inventory_component_id,
            serial_number=it.serial_number,
            status=it.status.status_name if it.status else "",
            notes=it.notes,
        ) for it in items]

    def update_item(self, db: Session, item_id: int, data: ItemUpdate) -> ItemResponse:
        item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
        if not item:
            raise HTTPException(status_code=404, detail="Item tidak ditemukan")
        if data.serial_number is not None:
            item.serial_number = data.serial_number
        db.commit()
        db.refresh(item)
        return ItemResponse(
            id=item.id, inventory_component_id=item.inventory_component_id,
            serial_number=item.serial_number,
            status=item.status.status_name if item.status else "",
            notes=item.notes,
        )

    def delete_item(self, db: Session, item_id: int) -> dict:
        """Hapus item individual. Hanya item dengan status Available atau Broken yang bisa dihapus."""
        item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
        if not item:
            raise HTTPException(status_code=404, detail="Item tidak ditemukan")

        status_name = item.status.status_name if item.status else ""
        if status_name not in ("Available", "Broken"):
            raise HTTPException(
                status_code=409,
                detail=f"Item tidak bisa dihapus — status '{status_name}'. Hanya item Available dan Broken yang bisa dihapus.",
            )

        cid = item.inventory_component_id
        comp = self.comp_repo.get(db, cid)
        if not comp:
            raise HTTPException(status_code=404, detail="Unit tidak ditemukan")

        # Kurangi total_quantity
        comp.total_quantity = max(0, comp.total_quantity - 1)

        # Hapus item
        db.delete(item)
        db.flush()

        # Recompute status komponen
        self.recompute_component_status(db, cid)

        db.commit()
        return {"status": "success", "message": f"Item SN '{item.serial_number or '-'}' berhasil dihapus"}

    def update_item_status(self, db: Session, item_id: int, status_name: str) -> None:
        from app.models.inventory_status import InventoryStatus
        item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
        if not item:
            return
        st = db.query(InventoryStatus).filter(InventoryStatus.status_name == status_name).first()
        if st:
            item.status_id = st.id

    def recompute_component_status(self, db: Session, component_id: int) -> None:
        from app.models.inventory_status import InventoryStatus
        comp = self.comp_repo.get(db, component_id)
        if not comp:
            return
        items = db.query(InventoryItem).filter(
            InventoryItem.inventory_component_id == component_id
        ).all()
        if not items:
            return

        statuses = db.query(InventoryStatus).all()
        status_map = {s.status_name: s.id for s in statuses}

        item_status_names = [it.status.status_name for it in items]

        if "Available" in item_status_names:
            comp.status_id = status_map.get("Available", comp.status_id)
        elif "Maintenance" in item_status_names:
            comp.status_id = status_map.get("Maintenance", comp.status_id)
        elif "Borrowed" in item_status_names:
            comp.status_id = status_map.get("Borrowed", comp.status_id)

        db.commit()

    # ── Template Excel ──

    HEADERS = [
        "nama_unit", "merek", "model", "spesifikasi", "serial_number",
        "quantity", "tahun_pengadaan", "supplier", "divisi", "catatan",
    ]

    def generate_template(self) -> BytesIO:
        """Generate file .xlsx template dengan 1 sheet contoh."""
        wb = Workbook()
        ws = wb.active
        ws.title = "Contoh_Nama_Unit"  # placeholder, user akan ganti

        # Header
        for col_idx, header in enumerate(self.HEADERS, 1):
            ws.cell(row=1, column=col_idx, value=header)

        # Contoh data
        example = ["Sensor Suhu", "Campbell", "CS215", "Sensor suhu digital -40°C s.d 60°C",
                     "SN-2024-001", 5, 2024, "PT. Alat Sensor", "Gempa Bumi", ""]
        for col_idx, val in enumerate(example, 1):
            ws.cell(row=2, column=col_idx, value=val)

        # Set column widths
        for col_idx in range(1, len(self.HEADERS) + 1):
            ws.column_dimensions[ws.cell(row=1, column=col_idx).column_letter].width = 18

        output = BytesIO()
        wb.save(output)
        output.seek(0)
        return output

    def import_from_excel(self, db: Session, file: UploadFile) -> dict:
        """Import komponen dari file .xlsx. Setiap sheet = 1 komponen."""
        if not file.filename.endswith(('.xlsx', '.xlsm')):
            raise HTTPException(status_code=400, detail="File harus berformat .xlsx")

        try:
            contents = file.file.read()
            wb = load_workbook(filename=BytesIO(contents), read_only=True, data_only=True)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Gagal membaca file Excel: {e}")

        created = 0
        errors = []

        for sheet_name in wb.sheetnames:
            ws = wb[sheet_name]

            # Skip sheet template yang masih punya nama placeholder
            if sheet_name == "Contoh_Nama_Unit":
                continue

            # Ambil header dari baris 1
            headers = []
            for col in range(1, len(self.HEADERS) + 1):
                val = ws.cell(row=1, column=col).value
                headers.append(str(val).strip().lower() if val else "")

            # Ambil data dari baris 2
            row_data = {}
            for col_idx, header in enumerate(headers, 1):
                val = ws.cell(row=2, column=col_idx).value
                row_data[header] = val

            # Validasi
            item_name = str(row_data.get("nama_unit", "")).strip() or str(sheet_name).strip()
            if not item_name:
                errors.append(f"Sheet '{sheet_name}': Nama Unit kosong, dilewati")
                continue

            specs = str(row_data.get("spesifikasi", "")).strip()
            if not specs:
                specs = ""  # Optional now, provide empty default

            try:
                quantity = int(row_data.get("quantity", 0))
            except (ValueError, TypeError):
                quantity = 0
            if quantity < 1:
                errors.append(f"Sheet '{sheet_name}': Quantity tidak valid ({row_data.get('quantity')}), dilewati")
                continue

            # Parse tahun
            procurement_year = None
            try:
                py_val = row_data.get("tahun_pengadaan")
                if py_val is not None and str(py_val).strip():
                    procurement_year = int(py_val)
            except (ValueError, TypeError):
                procurement_year = None

            # Buat komponen
            try:
                # Auto-generate serial numbers jika tidak disediakan
                sn_list = [f"{item_name}-{i+1:03d}" for i in range(quantity)]

                comp_data = ComponentCreate(
                    item_name=item_name,
                    brand=str(row_data.get("merek", "")).strip() or item_name,
                    model=str(row_data.get("model", "")).strip() or "-",
                    serial_number=str(row_data.get("serial_number", "")).strip() or None,
                    procurement_year=procurement_year,
                    supplier=str(row_data.get("supplier", "")).strip() or None,
                    total_quantity=quantity,
                    specifications=specs,
                    division=str(row_data.get("divisi", "")).strip() or "Gempa Bumi",
                    serial_numbers=sn_list,
                    notes=str(row_data.get("catatan", "")).strip() or None,
                )
                self.create_component(db, comp_data)
                created += 1
            except Exception as e:
                errors.append(f"Sheet '{sheet_name}': Gagal membuat komponen — {str(e)}")

        wb.close()

        return {
            "status": "success",
            "message": f"Berhasil import {created} komponen",
            "created": created,
            "errors": errors,
        }
