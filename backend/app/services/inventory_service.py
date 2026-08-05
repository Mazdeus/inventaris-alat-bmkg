"""InventoryService — logika bisnis untuk komponen inventaris."""
import re
from io import BytesIO

from fastapi import HTTPException, UploadFile
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation
from sqlalchemy.orm import Session

from app.models.inventory_component import InventoryComponent
from app.models.inventory_item import InventoryItem
from app.models.inventory_status import InventoryStatus
from app.models.item_status_history import ItemStatusHistory
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
                    detail=f"Tidak bisa mengurangi quantity karena hanya {len(items_to_delete)} barang tersedia (sisanya sedang dipinjam/diperbaiki)"
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
            raise HTTPException(status_code=409, detail="Unit tidak bisa dihapus karena sedang dipinjam")
        if hasattr(comp, 'items') and comp.items:
            for item in comp.items:
                db.delete(item)
        self.comp_repo.delete(db, component_id)
        return {"status": "success", "message": f"Unit '{comp.item_name}' berhasil dihapus"}

    # ── Item (per barang fisik) ──

    def _write_history(self, db: Session, *, item_id: int, component_id: int,
                       from_status_id: int | None, to_status_id: int, source: str,
                       return_id: int | None = None, borrow_id: int | None = None,
                       user_id: int | None = None, notes: str | None = None) -> None:
        """Catat riwayat perubahan status ke tabel item_status_history."""
        h = ItemStatusHistory(
            inventory_item_id=item_id,
            inventory_component_id=component_id,
            from_status_id=from_status_id,
            to_status_id=to_status_id,
            source=source,
            return_id=return_id,
            borrow_transaction_id=borrow_id,
            user_id=user_id,
            notes=notes,
        )
        db.add(h)

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
        if data.status_id is not None:
            old_status_id = item.status_id  # simpan sebelum diubah
            # Validasi: hanya boleh ganti antara Available dan Broken
            status = db.query(InventoryStatus).filter(InventoryStatus.id == data.status_id).first()
            if not status:
                raise HTTPException(status_code=400, detail="Status tidak valid")
            if status.status_name not in ("Available", "Broken"):
                raise HTTPException(
                    status_code=400,
                    detail=f"Status '{status.status_name}' tidak diizinkan. Hanya Tersedia (Available) atau Rusak (Broken) yang bisa diatur manual.",
                )
            # Cegah mengubah item yang sedang Borrowed/Maintenance ke Available/Broken
            current_status = item.status.status_name if item.status else ""
            if current_status in ("Borrowed", "Maintenance"):
                raise HTTPException(
                    status_code=409,
                    detail=f"Item berstatus '{current_status}'. Ubah status hanya bisa untuk item Tersedia atau Rusak.",
                )
            item.status_id = data.status_id
        db.commit()
        db.refresh(item)
        # Recompute status komponen jika status item berubah
        if data.status_id is not None:
            self._write_history(db,
                item_id=item.id, component_id=item.inventory_component_id,
                from_status_id=old_status_id,
                to_status_id=data.status_id, source="ADMIN_TOGGLE",
                user_id=None,
            )
            self.recompute_component_status(db, item.inventory_component_id)
        return ItemResponse(
            id=item.id, inventory_component_id=item.inventory_component_id,
            serial_number=item.serial_number,
            status=item.status.status_name if item.status else "",
            notes=item.notes,
        )

    def delete_item(self, db: Session, item_id: int) -> dict:
        """Soft delete item — ubah status jadi Dihapuskan. Hanya item Available/Broken yang bisa dihapus."""
        from datetime import datetime

        item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
        if not item:
            raise HTTPException(status_code=404, detail="Item tidak ditemukan")

        status_name = item.status.status_name if item.status else ""
        if status_name not in ("Available", "Broken"):
            raise HTTPException(
                status_code=409,
                detail=f"Item tidak bisa dihapus karena status '{status_name}'. Hanya item Tersedia dan Rusak yang bisa dihapus.",
            )

        cid = item.inventory_component_id
        comp = self.comp_repo.get(db, cid)
        if not comp:
            raise HTTPException(status_code=404, detail="Unit tidak ditemukan")

        # Kurangi total_quantity
        comp.total_quantity = max(0, comp.total_quantity - 1)

        # Cari status Dihapuskan
        deleted_status = db.query(InventoryStatus).filter(
            InventoryStatus.status_name == "Dihapuskan"
        ).first()
        if not deleted_status:
            raise HTTPException(status_code=500, detail="Status 'Dihapuskan' tidak ditemukan. Jalankan seed/migrasi terlebih dahulu.")

        old_status_id = item.status_id
        sn = item.serial_number or f"#{item.id}"

        # Soft delete: ubah status + set deleted_at
        item.status_id = deleted_status.id
        item.deleted_at = datetime.utcnow()

        # Catat history
        self._write_history(db,
            item_id=item.id, component_id=cid,
            from_status_id=old_status_id, to_status_id=deleted_status.id,
            source="DELETE", user_id=None,
        )

        # Recompute status komponen (skip item Dihapuskan)
        self.recompute_component_status(db, cid)

        db.commit()
        return {"status": "success", "message": f"Item {sn} berhasil dihapuskan"}

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

        item_status_names = [it.status.status_name for it in items
                             if it.status and it.status.status_name != "Dihapuskan"]

        if "Available" in item_status_names:
            comp.status_id = status_map.get("Available", comp.status_id)
        elif "Maintenance" in item_status_names:
            comp.status_id = status_map.get("Maintenance", comp.status_id)
        elif "Borrowed" in item_status_names:
            comp.status_id = status_map.get("Borrowed", comp.status_id)
        else:
            # Semua item Broken atau status lain → komponen jadi Broken
            comp.status_id = status_map.get("Broken", comp.status_id)

        db.commit()

    # ── Template Excel ──

    # Mapping label sheet → field key (case-insensitive, whitespace-normalized)
    LABEL_MAP = {
        "nama unit": "item_name",
        "nama unit (wajib)": "item_name",
        "merek": "brand",
        "merek (wajib)": "brand",
        "model": "model",
        "model (wajib)": "model",
        "spesifikasi": "specifications",
        "tahun pengadaan": "procurement_year",
        "tahun pengadaan (wajib)": "procurement_year",
        "supplier": "supplier",
        "divisi": "division",
        "divisi (wajib)": "division",
        "jumlah total": "total_quantity",
        "jumlah total (wajib)": "total_quantity",
        "catatan": "notes",
    }

    DIVISI_VALID = frozenset({"Gempa Bumi", "Tsunami", "Percepatan Tanah"})
    REQUIRED_FIELDS = frozenset({"item_name", "brand", "model", "procurement_year", "division", "total_quantity"})

    def _clean_label(self, label: str) -> str:
        """Normalize label: lowercase, collapse whitespace, strip trailing *."""
        return re.sub(r'\s+', ' ', str(label).strip().lower().rstrip("*"))

    def generate_template(self) -> BytesIO:
        """Generate template .xlsx: 1 sheet Petunjuk + 5 sheet unit kosong (format form)."""
        wb = Workbook()

        # ── Shared styles ──
        header_font = Font(name="Calibri", bold=True, size=14)
        section_font = Font(name="Calibri", bold=True, size=11)
        label_font = Font(name="Calibri", bold=True, size=10)
        label_required = Font(name="Calibri", bold=True, size=10, color="C00000")
        normal_font = Font(name="Calibri", size=10)
        thin_border = Border(
            left=Side(style="thin"), right=Side(style="thin"),
            top=Side(style="thin"), bottom=Side(style="thin"),
        )
        header_fill = PatternFill(start_color="D9E2F3", end_color="D9E2F3", fill_type="solid")

        # ── Sheet: Petunjuk ──
        ws_pet = wb.active
        ws_pet.title = "Petunjuk"
        ws_pet.column_dimensions["A"].width = 85

        pet_rows = [
            ("PETUNJUK PENGISIAN TEMPLATE IMPORT UNIT INVENTARIS", header_font),
            (),
            ("Format Template:", section_font),
            ("• Setiap sheet (kecuali sheet \"Petunjuk\" ini) mewakili 1 (satu) unit inventaris.", normal_font),
            ("• Sheet \"Petunjuk\" ini TIDAK akan diproses saat import.", normal_font),
            (),
            ("Cara Pengisian:", section_font),
            ("1. Pilih sheet Unit_1, Unit_2, … untuk mengisi data unit yang ingin ditambahkan.", normal_font),
            ("2. Isi nilai di KOLOM B. KOLOM A adalah label/nama field. JANGAN DIUBAH.", normal_font),
            ("3. Field bertanda (Wajib) dan berwarna merah HARUS diisi.", normal_font),
            ("4. Isi Nomor Seri (SN) untuk SETIAP barang fisik. Jumlah SN harus SAMA PERSIS dengan Jumlah Total.", normal_font),
            ("5. Jika jumlah barang lebih dari yang tersedia, tambahkan baris baru di bawah daftar Nomor Seri.", normal_font),
            ("6. Nomor seri TIDAK BOLEH kosong dan TIDAK BOLEH duplikat (dalam satu file).", normal_font),
            ("7. Simpan file, lalu upload melalui tombol \"Import Excel\".", normal_font),
            (),
            ("Field Wajib (harus diisi):", section_font),
            ("• Nama Unit          : nama unit inventaris (contoh: Sensor Suhu, Akselerograf)", normal_font),
            ("• Merek              : merek alat (contoh: Campbell, Kinemetrics)", normal_font),
            ("• Model              : tipe/model alat (contoh: CS215, ETNA 2)", normal_font),
            ("• Tahun Pengadaan    : tahun perolehan, format 4 digit (contoh: 2024)", normal_font),
            ("• Divisi             : pilih salah satu: Gempa Bumi / Tsunami / Percepatan Tanah", normal_font),
            ("• Jumlah Total       : jumlah barang fisik dalam unit ini (minimal 1)", normal_font),
            ("• Nomor Seri         : setiap barang wajib memiliki nomor seri unik", normal_font),
            (),
            ("Field Opsional:", section_font),
            ("• Spesifikasi        : deskripsi teknis alat", normal_font),
            ("• Supplier           : nama penyedia/pemasok alat", normal_font),
            ("• Catatan            : informasi tambahan", normal_font),
            (),
            ("Contoh Pengisian (Unit_1):", section_font),
            ("  Nama Unit          : Sensor Suhu", normal_font),
            ("  Merek              : Campbell", normal_font),
            ("  Model              : CS215", normal_font),
            ("  Spesifikasi        : Sensor suhu digital -40°C s.d 60°C", normal_font),
            ("  Tahun Pengadaan    : 2024", normal_font),
            ("  Supplier           : PT. Alat Sensor Indonesia", normal_font),
            ("  Divisi             : Gempa Bumi", normal_font),
            ("  Jumlah Total       : 5", normal_font),
            ("  Catatan            : Dipasang di Stasiun BMKG Bandung", normal_font),
            ("  Nomor Seri:", normal_font),
            ("    1. SN-CS215-001", normal_font),
            ("    2. SN-CS215-002", normal_font),
            ("    3. SN-CS215-003", normal_font),
            ("    4. SN-CS215-004", normal_font),
            ("    5. SN-CS215-005", normal_font),
        ]

        for i, row_data in enumerate(pet_rows, 1):
            if isinstance(row_data, tuple) and len(row_data) >= 2:
                value, font = row_data
            elif isinstance(row_data, tuple) and len(row_data) >= 1:
                value, font = row_data[0], normal_font
            else:
                value, font = ("", normal_font)
            cell = ws_pet.cell(row=i, column=1, value=value if value else None)
            if font:
                cell.font = font

        ws_pet.protection.sheet = True

        # ── Unit sheets (Unit_1 … Unit_5) ──
        UNIT_FIELDS = [
            ("Nama Unit (Wajib)", True),
            ("Merek (Wajib)", True),
            ("Model (Wajib)", True),
            ("Spesifikasi", False),
            ("Tahun Pengadaan (Wajib)", True),
            ("Supplier", False),
            ("Divisi (Wajib)", True),
            ("Jumlah Total (Wajib)", True),
            ("Catatan", False),
        ]

        DIVISI_FORMULA = '"Gempa Bumi,Tsunami,Percepatan Tanah"'

        for sheet_idx in range(1, 6):
            ws = wb.create_sheet(title=f"Unit_{sheet_idx}")
            ws.column_dimensions["A"].width = 26
            ws.column_dimensions["B"].width = 48

            # Unit fields (rows 1-9)
            for row_idx, (label, required) in enumerate(UNIT_FIELDS, 1):
                label_cell = ws.cell(row=row_idx, column=1, value=label)
                label_cell.font = label_required if required else label_font
                label_cell.alignment = Alignment(vertical="center")

                val_cell = ws.cell(row=row_idx, column=2)
                val_cell.font = normal_font
                val_cell.border = thin_border

                if "Divisi" in label:
                    dv = DataValidation(type="list", formula1=DIVISI_FORMULA, allow_blank=True)
                    dv.error = "Pilih salah satu: Gempa Bumi / Tsunami / Percepatan Tanah"
                    dv.errorTitle = "Divisi Tidak Valid"
                    ws.add_data_validation(dv)
                    dv.add(val_cell)

                if "Tahun" in label or "Jumlah" in label:
                    val_cell.number_format = "0"

            # Separator (row 10)
            ws.cell(row=10, column=1).font = normal_font

            # SN section header (row 11)
            for col, (text, width) in enumerate([("No", None), ("Nomor Seri (Wajib)", None)], 1):
                hdr = ws.cell(row=11, column=col, value=text)
                hdr.font = Font(name="Calibri", bold=True, size=10,
                                color="C00000" if col == 2 else "000000")
                hdr.fill = header_fill
                hdr.border = thin_border
                hdr.alignment = Alignment(horizontal="center")

            # SN input rows (12-21, 10 default rows)
            for i in range(10):
                row_num = 12 + i
                no_cell = ws.cell(row=row_num, column=1, value=i + 1)
                no_cell.font = normal_font
                no_cell.alignment = Alignment(horizontal="center")
                no_cell.border = thin_border

                sn_cell = ws.cell(row=row_num, column=2)
                sn_cell.font = normal_font
                sn_cell.border = thin_border

        output = BytesIO()
        wb.save(output)
        output.seek(0)
        return output

    def import_from_excel(self, db: Session, file: UploadFile) -> dict:
        """Import komponen dari file .xlsx. Setiap sheet = 1 komponen.

        Format per sheet (form layout):
        - Kolom A: label field, Kolom B: nilai
        - Baris 1-9: field unit
        - Baris 11: header No | Nomor Seri
        - Baris 12+: daftar nomor seri (satu per baris)
        """
        if not file.filename.endswith(('.xlsx', '.xlsm')):
            raise HTTPException(status_code=400, detail="File harus berformat .xlsx atau .xlsm")

        try:
            contents = file.file.read()
            wb = load_workbook(filename=BytesIO(contents), read_only=False, data_only=True)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Gagal membaca file Excel: {e}")

        created = 0
        total_sheets = 0
        errors = []
        all_sns_seen: set[str] = set()  # deteksi duplikat SN antar sheet

        for sheet_name in wb.sheetnames:
            if sheet_name.lower() == "petunjuk":
                continue

            total_sheets += 1
            ws = wb[sheet_name]

            # ── Parse unit fields dari kolom A-B baris 1-9 ──
            row_data: dict[str, str] = {}
            for row_idx in range(1, 10):
                label_val = ws.cell(row=row_idx, column=1).value
                field_val = ws.cell(row=row_idx, column=2).value
                if label_val is None:
                    continue
                key = self.LABEL_MAP.get(self._clean_label(str(label_val)))
                if key:
                    row_data[key] = str(field_val).strip() if field_val is not None else ""

            # ── Parse serial numbers dari baris 12+ kolom B ──
            serial_numbers: list[str] = []
            row_idx = 12
            while True:
                val = ws.cell(row=row_idx, column=2).value
                if val is None or str(val).strip() == "":
                    break
                serial_numbers.append(str(val).strip())
                row_idx += 1

            # ── Validasi ──
            sheet_errors: list[str] = []

            item_name = row_data.get("item_name", "").strip()
            if not item_name:
                item_name = str(sheet_name).strip()
            if not item_name:
                errors.append(f"Sheet '{sheet_name}': Nama Unit kosong, dilewati")
                continue

            brand = row_data.get("brand", "").strip()
            if not brand:
                sheet_errors.append("Merek kosong")

            model = row_data.get("model", "").strip()
            if not model:
                sheet_errors.append("Model kosong")

            specs = row_data.get("specifications", "").strip()

            procurement_year = 0
            py_str = row_data.get("procurement_year", "").strip()
            if not py_str:
                sheet_errors.append("Tahun Pengadaan kosong")
            else:
                try:
                    procurement_year = int(float(py_str))
                    if procurement_year < 2000 or procurement_year > 2100:
                        sheet_errors.append(f"Tahun Pengadaan '{py_str}' di luar rentang 2000-2100")
                except (ValueError, TypeError):
                    sheet_errors.append(f"Tahun Pengadaan '{py_str}' tidak valid (harus angka 4 digit)")

            supplier = row_data.get("supplier", "").strip() or None

            division = row_data.get("division", "").strip()
            if not division:
                sheet_errors.append("Divisi kosong")
            elif division not in self.DIVISI_VALID:
                sheet_errors.append(
                    f"Divisi '{division}' tidak valid (harus: Gempa Bumi / Tsunami / Percepatan Tanah)"
                )

            quantity = 0
            qty_str = row_data.get("total_quantity", "").strip()
            if not qty_str:
                sheet_errors.append("Jumlah Total kosong")
            else:
                try:
                    quantity = int(float(qty_str))
                    if quantity < 1:
                        sheet_errors.append(f"Jumlah Total '{qty_str}' harus >= 1")
                except (ValueError, TypeError):
                    sheet_errors.append(f"Jumlah Total '{qty_str}' tidak valid (harus angka)")

            notes = row_data.get("notes", "").strip() or None

            if sheet_errors:
                errors.append(f"Sheet '{sheet_name}': {'; '.join(sheet_errors)}. Dilewati.")
                continue

            # ── Validasi Nomor Seri ──
            if not serial_numbers:
                errors.append(f"Sheet '{sheet_name}': Nomor Seri kosong, dilewati")
                continue

            if len(serial_numbers) != quantity:
                errors.append(
                    f"Sheet '{sheet_name}': Jumlah Nomor Seri ({len(serial_numbers)}) "
                    f"tidak sesuai dengan Jumlah Total ({quantity}), dilewati"
                )
                continue

            # Cek SN kosong
            empty_idxs = [i + 1 for i, sn in enumerate(serial_numbers) if not sn]
            if empty_idxs:
                errors.append(
                    f"Sheet '{sheet_name}': Nomor Seri ke-{', '.join(map(str, empty_idxs))} kosong, dilewati"
                )
                continue

            # Cek duplikat dalam satu sheet
            seen_local: set[str] = set()
            local_dupes: list[str] = []
            for sn in serial_numbers:
                if sn in seen_local:
                    local_dupes.append(sn)
                seen_local.add(sn)

            if local_dupes:
                errors.append(
                    f"Sheet '{sheet_name}': Nomor Seri duplikat dalam satu unit: "
                    f"{', '.join(dict.fromkeys(local_dupes))}. Dilewati."
                )
                continue

            # Cek duplikat antar sheet (dalam satu file)
            cross_dupes = [sn for sn in serial_numbers if sn in all_sns_seen]
            if cross_dupes:
                errors.append(
                    f"Sheet '{sheet_name}': Nomor Seri sudah digunakan di unit lain: "
                    f"{', '.join(dict.fromkeys(cross_dupes))}. Dilewati."
                )
                continue

            all_sns_seen.update(serial_numbers)

            # ── Buat komponen ──
            try:
                comp_data = ComponentCreate(
                    item_name=item_name,
                    brand=brand,
                    model=model,
                    serial_number=None,
                    procurement_year=procurement_year,
                    supplier=supplier,
                    total_quantity=quantity,
                    specifications=specs,
                    division=division,
                    serial_numbers=serial_numbers,
                    notes=notes,
                )
                self.create_component(db, comp_data)
                created += 1
            except HTTPException as he:
                errors.append(f"Sheet '{sheet_name}': Gagal membuat unit: {he.detail}")
            except Exception as e:
                errors.append(f"Sheet '{sheet_name}': Gagal membuat unit: {str(e)}")

        wb.close()

        if created == 0 and not errors:
            errors.append(
                "Tidak ada data unit yang valid untuk diimpor. "
                "Pastikan sheet (selain Petunjuk) berisi data sesuai format template."
            )

        return {
            "status": "success",
            "message": f"Berhasil import {created} unit dari {total_sheets} sheet",
            "created": created,
            "total_sheets": total_sheets,
            "errors": errors,
        }
