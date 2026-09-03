import api from "./axios";
import { compressImage } from "@/lib/imageCompressor";

/**
 * Upload file gambar ke server (dengan kompresi otomatis client-side jika ukuran besar).
 * @param {File} file - File gambar yang akan diupload
 * @returns {Promise<{url: string, absolute_path: string, full_url: string}>} Object dengan 3 path
 */
export async function uploadPhoto(file) {
  const processedFile = await compressImage(file);
  const formData = new FormData();
  formData.append("file", processedFile);
  const res = await api.post("/uploads", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return res.data.data; // { url, absolute_path, full_url }
}

