"""Endpoint untuk upload file (foto dokumentasi)."""
from fastapi import APIRouter, Depends, File, UploadFile

from app.core.dependencies import get_current_user
from app.core.upload import save_upload
from app.models.user import User

router = APIRouter(prefix="/api/v1/uploads", tags=["Uploads"])


@router.post("")
async def upload_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    """Upload file gambar (jpg, jpeg, png, webp) maks 5 MB.
    Mengembalikan URL absolut dan path absolut."""
    result = save_upload(file, "general")
    return {"status": "success", "message": "File berhasil diupload", "data": result}
