import api from "./axios";

/**
 * Upload file gambar ke server.
 * @param {File} file - File gambar yang akan diupload
 * @returns {Promise<{url: string, absolute_path: string, full_url: string}>} Object dengan 3 path
 */
export async function uploadPhoto(file) {
  const formData = new FormData();
  formData.append("file", file);
  const res = await api.post("/uploads", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return res.data.data; // { url, absolute_path, full_url }
}
