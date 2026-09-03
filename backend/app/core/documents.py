"""Generate dokumen verifikasi (Berita Acara Serah Terima Barang) dalam bentuk PDF.

Dokumen terdiri atas 3 halaman:
1. Halaman judul — kop BMKG, judul BAST, tanggal, identitas kedua pihak, Pasal 1-3.
2. Pernyataan penutup + kolom tanda tangan.
3. Lampiran daftar barang (No, Nama Barang, Merk, Type, Jumlah, Serial Number,
   ditambah kolom Kondisi untuk pengembalian).

Deskripsi barang dan tujuan peminjaman diambil dari transaksi peminjaman
(field `item_description` dan `purpose`), bukan teks hardcode.
"""
import math
import struct
from pathlib import Path

from fpdf import FPDF

ASSETS_DIR = Path(__file__).resolve().parent.parent.parent / "assets"
LOGO_PATH = ASSETS_DIR / "logo_bmkg.png"

MONTHS_ID = [
    "Januari", "Februari", "Maret", "April", "Mei", "Juni",
    "Juli", "Agustus", "September", "Oktober", "November", "Desember",
]

TITLE_BORROW = "BERITA ACARA SERAH TERIMA BARANG"
TITLE_RETURN = "BERITA ACARA SERAH TERIMA BARANG (PENGEMBALIAN)"


def _format_date_id(d):
    if not d:
        return "-"
    return f"{d.day} {MONTHS_ID[d.month - 1]} {d.year}"


def _png_size(path) -> tuple | None:
    """Baca dimensi (width, height) dalam piksel dari file PNG."""
    try:
        with open(path, "rb") as f:
            data = f.read(26)
        if data[:8] != b"\x89PNG\r\n\x1a\n":
            return None
        w, h = struct.unpack(">II", data[16:24])
        return w, h
    except Exception:
        return None


class BASTPDF(FPDF):
    """PDF BAST dengan header kop dan bantuan tabel."""

    def header(self):
        # Kop hanya ditampilkan di halaman pertama
        if self.page_no() > 1:
            return
        if LOGO_PATH.exists():
            size = _png_size(LOGO_PATH)
            if size and size[0] > 0:
                w_px, h_px = size
                h = self.epw * (h_px / w_px)
                try:
                    self.image(str(LOGO_PATH), x=15, y=8, w=self.epw, h=h)
                    self.set_y(8 + h + 2)
                    return
                except Exception:
                    pass
        self._text_header()

    def _text_header(self):
        self.set_font("Helvetica", "B", 14)
        self.cell(0, 7, "BADAN METEOROLOGI, KLIMATOLOGI, DAN GEOFISIKA", ln=1, align="C")
        self.set_font("Helvetica", "", 9)
        self.cell(0, 5, "SISTEM INVENTARIS ALAT SENSOR BMKG", ln=1, align="C")
        self.ln(2)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.cell(0, 10, f"Halaman {self.page_no()}", align="C")

    def _line_height(self, text: str, width: float, font_size: float) -> int:
        """Hitung jumlah baris yang dibutuhkan teks pada lebar kolom tertentu."""
        if not text:
            return 1
        padding = 1.6
        available = max(width - padding, 1)
        lines = 0
        for seg in str(text).split("\n"):
            lines += max(1, math.ceil(self.get_string_width(seg) / available))
        return lines

    def table_row(self, widths, cells, line_h=5, align=("C", "L", "L", "L", "C")):
        """Gambar satu baris tabel dengan tinggi yang menyesuaikan isi dan border rata."""
        x_start = self.get_x()
        y_start = self.get_y()

        # Hitung tinggi maksimum antar sel
        max_lines = 1
        for i, txt in enumerate(cells):
            max_lines = max(max_lines, self._line_height(str(txt or ""), widths[i], self.font_size))
        row_h = max_lines * line_h

        # Page break jika melebihi batas
        if y_start + row_h > self.eph:
            self.add_page()
            x_start = self.get_x()
            y_start = self.get_y()

        for i, txt in enumerate(cells):
            x = x_start + sum(widths[:i])
            # Gambar kotak border penuh setinggi row_h
            self.rect(x, y_start, widths[i], row_h)
            self.set_xy(x, y_start)
            a = align[i] if i < len(align) else "L"
            self.multi_cell(widths[i], line_h, str(txt if txt is not None else ""),
                            border=0, align=a)

        self.set_xy(x_start, y_start + row_h)


def _new_pdf() -> BASTPDF:
    pdf = BASTPDF(orientation="P", unit="mm", format="A4")
    pdf.set_margins(15, 15, 15)
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.set_font("Helvetica", "", 10)
    return pdf


def _party_block(pdf: BASTPDF, label: str, name: str, id_no: str, position: str, institution: str):
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, label, ln=1)
    pdf.set_font("Helvetica", "", 10)
    rows = [
        ("Nama", name or "-"),
        ("NIP/NIK", id_no or "-"),
        ("Jabatan", position or "-"),
        ("Instansi/Unit", institution or "-"),
    ]
    for k, v in rows:
        pdf.set_font("Helvetica", "B", 10)
        w = pdf.get_string_width(f"{k}: ")
        pdf.cell(w, 6, f"{k}: ")
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(0, 6, v, ln=1)
    pdf.ln(2)


def _signature_block(pdf: BASTPDF, left_label: str, left_name: str, left_id: str,
                     right_label: str, right_name: str, right_id: str):
    half = pdf.epw / 2

    def row(left_text: str, right_text: str, bold: bool = False):
        y = pdf.get_y()
        pdf.set_font("Helvetica", "B" if bold else "", 10)
        pdf.set_xy(pdf.l_margin, y)
        pdf.cell(half, 6, left_text, align="C")
        pdf.set_xy(pdf.l_margin + half, y)
        pdf.cell(half, 6, right_text, align="C")
        pdf.ln(6)

    row(left_label, right_label, bold=True)
    row("", "")
    row("", "")
    row("", "")
    row(left_name or "", right_name or "")
    row(f"NIP. {left_id}" if left_id else "", f"NIP. {right_id}" if right_id else "")

    pdf.ln(4)


def _draw_attachment(pdf: BASTPDF, rows, with_condition: bool, date_val):
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Lampiran", ln=1, align="C")
    pdf.cell(0, 6, "Berita Acara Serah Terima Barang", ln=1, align="C")
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(0, 5, f"Tanggal : {_format_date_id(date_val)}", ln=1, align="C")
    pdf.ln(3)

    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(0, 6, "Daftar Barang dalam Kegiatan ini", ln=1)
    pdf.ln(1)

    # Lebar kolom (total = 180 mm = epw A4 dgn margin 15)
    if with_condition:
        widths = (10, 34, 22, 24, 14, 42, 34)
        headers = ["No", "Nama Barang", "Merk", "Type", "Jumlah", "Serial Number", "Kondisi"]
        aligns = ("CENTER", "LEFT", "LEFT", "LEFT", "CENTER", "LEFT", "LEFT")
    else:
        widths = (10, 40, 26, 28, 18, 58)
        headers = ["No", "Nama Barang", "Merk", "Type", "Jumlah", "Serial Number"]
        aligns = ("CENTER", "LEFT", "LEFT", "LEFT", "CENTER", "LEFT")

    with pdf.table(col_widths=widths, text_align=aligns, line_height=5) as table:
        header_row = table.row()
        pdf.set_font("Helvetica", "B", 9)
        for h in headers:
            header_row.cell(h)

        pdf.set_font("Helvetica", "", 9)
        for idx, row in enumerate(rows, 1):
            data_row = table.row()
            data_row.cell(str(idx))
            for cell_val in row:
                data_row.cell(str(cell_val if cell_val is not None else "-"))



def _render_document(pdf: BASTPDF, title: str, date_val,
                     party1: dict, party2: dict,
                     description: str, purpose: str,
                     article1_text: str, article2_text: str,
                     rows, with_condition: bool,
                     sign_left_label: str, sign_left_name: str, sign_left_id: str,
                     sign_right_label: str, sign_right_name: str, sign_right_id: str):
    pdf.add_page()

    # Judul & tanggal
    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 9, title, ln=1, align="C")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, f"Pada Tanggal {_format_date_id(date_val)}, kami yang bertanda tangan di bawah ini:", ln=1, align="L")
    pdf.ln(3)

    # Pihak
    _party_block(pdf, "1. PIHAK PERTAMA", party1["name"], party1["id_no"],
                 party1["position"], party1["institution"])
    _party_block(pdf, "2. PIHAK KEDUA", party2["name"], party2["id_no"],
                 party2["position"], party2["institution"])

    # Pasal
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, "Pasal 1", ln=1)
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 6, article1_text, align="J")
    pdf.ln(2)

    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, "Pasal 2", ln=1)
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 6, article2_text, align="J")
    pdf.ln(2)

    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, "Pasal 3", ln=1)
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 6,
                   "Lampiran Berita Acara Serah Terima yang ditandatangani oleh PIHAK PERTAMA dan "
                   "PIHAK KEDUA, merupakan bagian yang tidak terpisahkan dalam Berita Acara ini.",
                   align="J")

    # Halaman 2 — penutup + tanda tangan
    pdf.add_page()
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 6,
                   "Demikian Serah Terima Barang ini kami selenggarakan dengan seksama dan dalam keadaan "
                   "sebenarnya pada hari dan tanggal tersebut di atas untuk dipergunakan sebagaimana perlunya. "
                   "Berita Acara Serah Terima ini akan ditinjau kembali apabila dikemudian hari ternyata "
                   "terdapat kekeliruan.",
                   align="J")
    pdf.ln(14)
    _signature_block(pdf, sign_left_label, sign_left_name, sign_left_id,
                     sign_right_label, sign_right_name, sign_right_id)

    # Halaman 3 — lampiran
    pdf.add_page()
    _draw_attachment(pdf, rows, with_condition, date_val)

    pdf.ln(14)
    _signature_block(pdf, sign_left_label, sign_left_name, sign_left_id,
                     sign_right_label, sign_right_name, sign_right_id)

    return bytes(pdf.output())


def _officer_dict(officer) -> dict:
    if not officer:
        return {"name": "-", "id_no": "-", "position": "-", "institution": "-"}
    return {
        "name": officer.officer_name or "-",
        "id_no": officer.nip or "-",
        "position": officer.position or "-",
        "institution": officer.institution or "-",
    }


def _borrower_dict(borrower) -> dict:
    if not borrower:
        return {"name": "-", "id_no": "-", "position": "-", "institution": "-"}
    return {
        "name": borrower.borrower_name or "-",
        "id_no": borrower.nip or "-",
        "position": borrower.position or "-",
        "institution": borrower.institution or "-",
    }


def _borrow_rows(tx) -> list:
    rows = []
    for d in (tx.borrow_details or []):
        comp = d.inventory_component
        sns = [bdi.inventory_item.serial_number or "-"
               for bdi in (d.borrow_detail_items or []) if bdi.inventory_item]
        if not sns:
            sns = [comp.serial_number or "-"] if comp else ["-"]
        rows.append((
            comp.item_name if comp else "-",
            comp.brand if comp else "-",
            comp.model if comp else "-",
            str(d.quantity),
            "\n".join(sns),
        ))
    return rows


def _return_rows(ret) -> list:
    rows = []
    for d in (ret.return_details or []):
        comp = d.inventory_component
        sns = []
        conds = []
        for rdi in (d.return_detail_items or []):
            inv = rdi.inventory_item
            sns.append(inv.serial_number if inv and inv.serial_number else "-")
            conds.append(rdi.condition or "-")
        if not sns and comp:
            sns = [comp.serial_number or "-"]
            conds = ["-"]
        rows.append((
            comp.item_name if comp else "-",
            comp.brand if comp else "-",
            comp.model if comp else "-",
            str(d.quantity),
            "\n".join(sns),
            "\n".join(conds),
        ))
    return rows


def generate_borrow_document(tx) -> bytes:
    """Generate PDF BAST untuk peminjaman.

    Pihak Pertama = petugas (penyerah). Pihak Kedua = peminjam (penerima).
    """
    officer = _officer_dict(tx.officer)
    borrower = _borrower_dict(tx.borrower)
    description = tx.item_description or "-"
    purpose = tx.purpose or "-"

    pdf = _new_pdf()
    return _render_document(
        pdf=pdf,
        title=TITLE_BORROW,
        date_val=tx.borrow_date,
        party1=officer,
        party2=borrower,
        description=description,
        purpose=purpose,
        article1_text=(
            f"PIHAK PERTAMA menyerahkan kepada PIHAK KEDUA {description} "
            f"sebagaimana daftar terlampir."
        ),
        article2_text=(
            f"PIHAK KEDUA menerima {description} tersebut untuk digunakan dalam rangka "
            f"{purpose}."
        ),
        rows=_borrow_rows(tx),
        with_condition=False,
        sign_left_label="PIHAK KEDUA",
        sign_left_name=borrower["name"],
        sign_left_id=borrower["id_no"],
        sign_right_label="PIHAK PERTAMA",
        sign_right_name=officer["name"],
        sign_right_id=officer["id_no"],
    )


def generate_return_document(ret) -> bytes:
    """Generate PDF BAST untuk pengembalian.

    Pihak Pertama = peminjam (yang mengembalikan). Pihak Kedua = petugas (penerima).
    Tata letak tanda tangan dibalik: PIHAK PERTAMA kiri, PIHAK KEDUA kanan.
    """
    tx = ret.borrow_transaction
    officer = _officer_dict(ret.officer)
    borrower = _borrower_dict(tx.borrower if tx else None)
    description = (tx.item_description if tx else None) or "-"
    purpose = (tx.purpose if tx else None) or "-"

    pdf = _new_pdf()
    return _render_document(
        pdf=pdf,
        title=TITLE_RETURN,
        date_val=ret.return_date,
        party1=borrower,
        party2=officer,
        description=description,
        purpose=purpose,
        article1_text=(
            f"PIHAK PERTAMA menyerahkan kembali kepada PIHAK KEDUA {description} "
            f"sebagaimana daftar terlampir."
        ),
        article2_text=(
            f"PIHAK KEDUA menerima kembali {description} tersebut yang sebelumnya digunakan "
            f"dalam rangka {purpose}."
        ),
        rows=_return_rows(ret),
        with_condition=True,
        sign_left_label="PIHAK PERTAMA",
        sign_left_name=borrower["name"],
        sign_left_id=borrower["id_no"],
        sign_right_label="PIHAK KEDUA",
        sign_right_name=officer["name"],
        sign_right_id=officer["id_no"],
    )


TITLE_HANDOVER = "BERITA ACARA SERAH TERIMA BARANG (PELIMPAHAN)"


def _handover_rows(h) -> list:
    rows = []
    items_by_comp = {}
    for hi in (h.items or []):
        if hasattr(hi, "inventory_item") and hi.inventory_item:
            item = hi.inventory_item
            comp = item.component if hasattr(item, "component") else None
            comp_name = comp.item_name if comp else "-"
            brand = comp.brand if comp else "-"
            model = comp.model if comp else "-"
            sn = item.serial_number or "-"
        else:
            comp_name = getattr(hi, "component_name", "-") or "-"
            brand = "-"
            model = "-"
            sn = getattr(hi, "serial_number", "-") or "-"

        key = (comp_name, brand, model)
        if key not in items_by_comp:
            items_by_comp[key] = []
        items_by_comp[key].append(sn)

    for (comp_name, brand, model), sns in items_by_comp.items():
        rows.append((
            comp_name,
            brand,
            model,
            str(len(sns)),
            "\n".join(sns),
        ))
    return rows


def generate_handover_document(h) -> bytes:
    """Generate PDF BAST untuk pelimpahan barang ke UPT.

    Pihak Pertama = petugas (penyerah). Pihak Kedua = UPT Penerima.
    """
    officer = _officer_dict(h.officer if hasattr(h, "officer") else None)
    if hasattr(h, "officer_name") and h.officer_name and officer["name"] == "-":
        officer["name"] = h.officer_name

    upt_name = h.upt_receiver if hasattr(h, "upt_receiver") else "-"
    party2 = {
        "name": f"Pimpinan / Perwakilan {upt_name}",
        "id_no": "-",
        "position": "Penerima UPT",
        "institution": upt_name,
    }

    pdf = _new_pdf()
    return _render_document(
        pdf=pdf,
        title=TITLE_HANDOVER,
        date_val=h.handover_date,
        party1=officer,
        party2=party2,
        description="barang inventaris sebagaimana daftar terlampir",
        purpose=f"operasional dan pelayanan di lingkungan {upt_name}",
        article1_text=(
            f"PIHAK PERTAMA menyerahkan kepada PIHAK KEDUA barang inventaris "
            f"sebagaimana daftar terlampir."
        ),
        article2_text=(
            f"PIHAK KEDUA menerima barang inventaris tersebut untuk digunakan dalam rangka "
            f"operasional dan pelayanan di lingkungan {upt_name}."
        ),
        rows=_handover_rows(h),
        with_condition=False,
        sign_left_label="PIHAK KEDUA",
        sign_left_name=party2["name"],
        sign_left_id=party2["id_no"],
        sign_right_label="PIHAK PERTAMA",
        sign_right_name=officer["name"],
        sign_right_id=officer["id_no"],
    )

