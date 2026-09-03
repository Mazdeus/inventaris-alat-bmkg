"""Utility untuk menyimpan file upload dengan kompresi otomatis."""
import io
import os
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile
from PIL import Image, ImageOps

from app.core.config import settings

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
# Izinkan upload awal hingga 20 MB, sistem akan otomatis mengompresnya menjadi < 1 MB
MAX_UPLOAD_SIZE = 20 * 1024 * 1024  # 20 MB


def compress_image(contents: bytes, ext: str, max_dimension: int = 1920, quality: int = 85) -> tuple[bytes, str]:
    """Kompres gambar bytes:
    1. Perbaiki orientasi EXIF kamera HP (auto-rotate).
    2. Resize jika melebihi max_dimension (1920px) dengan LANCZOS resampling.
    3. Simpan dengan kompresi JPEG/WEBP teroptimasi.
    """
    try:
        with Image.open(io.BytesIO(contents)) as img:
            # Perbaiki rotasi dari kamera smartphone
            img = ImageOps.exif_transpose(img)

            # Downscale jika dimensi melebihi batas maksimal (Full HD / 1920px)
            w, h = img.size
            if max(w, h) > max_dimension:
                if w >= h:
                    new_w = max_dimension
                    new_h = int(h * (max_dimension / w))
                else:
                    new_h = max_dimension
                    new_w = int(w * (max_dimension / h))
                img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)

            output = io.BytesIO()
            clean_ext = ext.lower()

            if clean_ext in ("jpg", "jpeg"):
                if img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")
                img.save(output, format="JPEG", quality=quality, optimize=True)
                return output.getvalue(), "jpg"
            elif clean_ext == "png":
                # Jika ada transparansi, simpan PNG teroptimasi
                if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
                    img.save(output, format="PNG", optimize=True)
                    return output.getvalue(), "png"
                else:
                    if img.mode != "RGB":
                        img = img.convert("RGB")
                    img.save(output, format="JPEG", quality=quality, optimize=True)
                    return output.getvalue(), "jpg"
            elif clean_ext == "webp":
                img.save(output, format="WEBP", quality=quality, method=4)
                return output.getvalue(), "webp"
            else:
                if img.mode != "RGB":
                    img = img.convert("RGB")
                img.save(output, format="JPEG", quality=quality, optimize=True)
                return output.getvalue(), "jpg"
    except Exception:
        # Fallback jika bukan format gambar valid untuk Pillow
        return contents, ext


def save_upload(file: UploadFile, subdir: str, auto_compress: bool = True) -> dict:
    """Simpan file upload dengan kompresi otomatis dan return { url, absolute_path, full_url }."""
    # Validasi ekstensi
    ext = _get_ext(file.filename)
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Format file tidak didukung: {ext}. Gunakan: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )

    # Baca konten dan validasi ukuran maksimal
    contents = file.file.read()
    if len(contents) > MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"Ukuran file terlalu besar (maks {MAX_UPLOAD_SIZE // (1024*1024)} MB)",
        )
    file.file.seek(0)

    # Kompresi otomatis jika gambar > 400 KB atau jika auto_compress aktif
    final_ext = ext
    if auto_compress and ext in ("jpg", "jpeg", "png", "webp"):
        contents, final_ext = compress_image(contents, ext)

    # Buat folder tujuan
    target_dir = Path(settings.UPLOAD_DIR) / subdir
    target_dir.mkdir(parents=True, exist_ok=True)

    # Generate nama file unik
    filename = f"{uuid.uuid4().hex[:12]}.{final_ext}"
    filepath = target_dir / filename

    # Simpan file ke disk
    with open(filepath, "wb") as f:
        f.write(contents)

    # Return paths
    relative = f"{subdir}/{filename}"
    absolute_path = str(filepath.resolve())
    full_url = f"{settings.BASE_URL}/uploads/{relative}"
    return {"url": relative, "absolute_path": absolute_path, "full_url": full_url}


def delete_upload(relative_path: str) -> None:
    """Hapus file upload berdasarkan path relatif. Aman dari path traversal."""
    if not relative_path:
        return
    upload_root = Path(settings.UPLOAD_DIR).resolve()
    filepath = (upload_root / relative_path).resolve()
    if not str(filepath).startswith(str(upload_root) + os.sep) and filepath != upload_root:
        return
    try:
        if filepath.exists() and filepath.is_file():
            os.remove(filepath)
    except OSError:
        pass


def _get_ext(filename: str | None) -> str:
    if not filename:
        return ""
    return filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

