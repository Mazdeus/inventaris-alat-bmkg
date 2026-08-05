"""Utility untuk menyimpan file upload."""
import os
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile

from app.core.config import settings

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB


def save_upload(file: UploadFile, subdir: str) -> dict:
    """Simpan file upload dan return { url, absolute_path }.
    - url: full URL (contoh: http://localhost:8000/uploads/general/abc.jpg)
    - absolute_path: path absolut filesystem (contoh: C:/.../uploads/general/abc.jpg)
    """
    # Validasi ekstensi
    ext = _get_ext(file.filename)
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Format file tidak didukung: {ext}. Gunakan: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )

    # Baca konten dan validasi ukuran
    contents = file.file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"Ukuran file terlalu besar (maks {MAX_FILE_SIZE // (1024*1024)} MB)",
        )
    file.file.seek(0)  # reset untuk potensi upload ulang

    # Buat folder tujuan
    target_dir = Path(settings.UPLOAD_DIR) / subdir
    target_dir.mkdir(parents=True, exist_ok=True)

    # Generate nama file unik
    filename = f"{uuid.uuid4().hex[:12]}.{ext}"
    filepath = target_dir / filename

    # Simpan file
    with open(filepath, "wb") as f:
        f.write(contents)

    # Return all paths: url (relative), absolute_path, full_url
    relative = f"{subdir}/{filename}"
    absolute_path = str(filepath.resolve())
    full_url = f"{settings.BASE_URL}/uploads/{relative}"
    return {"url": relative, "absolute_path": absolute_path, "full_url": full_url}


def delete_upload(relative_path: str) -> None:
    """Hapus file upload berdasarkan path relatif. Aman dari path traversal."""
    if not relative_path:
        return
    # Resolve absolut path dalam UPLOAD_DIR, cegah traversal
    upload_root = Path(settings.UPLOAD_DIR).resolve()
    filepath = (upload_root / relative_path).resolve()
    # Pastikan filepath tetap di dalam UPLOAD_DIR
    if not str(filepath).startswith(str(upload_root) + os.sep) and filepath != upload_root:
        return  # path traversal detected, safely ignore
    try:
        if filepath.exists() and filepath.is_file():
            os.remove(filepath)
    except OSError:
        pass  # best-effort


def _get_ext(filename: str | None) -> str:
    if not filename:
        return ""
    return filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
