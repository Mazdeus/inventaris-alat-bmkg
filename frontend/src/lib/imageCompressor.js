/**
 * Utility kompresi gambar berbasis Native HTML5 Canvas API (Client-side).
 * Mengecilkan ukuran gambar secara instan di browser sebelum diunggah ke server.
 */

const DEFAULT_OPTIONS = {
  maxWidth: 1920,
  maxHeight: 1920,
  quality: 0.82,
  maxSizeMB: 1.5, // Hanya kompres jika ukuran file > 1.5 MB
};

/**
 * Kompres file gambar jika melebihi batas ukuran atau dimensi.
 *
 * @param {File} file - File objek dari input file
 * @param {Object} options - Konfigurasi kompresi
 * @returns {Promise<File>} File terkompresi atau file asli jika sudah kecil
 */
export async function compressImage(file, options = {}) {
  if (!file || !(file instanceof File)) {
    return file;
  }

  // Jika bukan file gambar (misal PDF atau dokumen lain), jangan diubah
  if (!file.type.startsWith("image/")) {
    return file;
  }

  const config = { ...DEFAULT_OPTIONS, ...options };
  const maxSizeBytes = config.maxSizeMB * 1024 * 1024;

  // Jika ukuran file sudah di bawah batas, tetap gunakan file asli
  if (file.size <= maxSizeBytes) {
    return file;
  }

  return new Promise((resolve) => {
    const reader = new FileReader();

    reader.onload = (e) => {
      const img = new Image();

      img.onload = () => {
        let width = img.width;
        let height = img.height;

        // Hitung skala rasio gambar
        if (width > config.maxWidth || height > config.maxHeight) {
          if (width / height > config.maxWidth / config.maxHeight) {
            height = Math.round((height * config.maxWidth) / width);
            width = config.maxWidth;
          } else {
            width = Math.round((width * config.maxHeight) / height);
            height = config.maxHeight;
          }
        }

        // Buat canvas untuk rendering
        const canvas = document.createElement("canvas");
        canvas.width = width;
        canvas.height = height;

        const ctx = canvas.getContext("2d");
        if (!ctx) {
          return resolve(file); // Fallback jika context gagal
        }

        // Gambar dengan smoothing berkualitas tinggi
        ctx.imageSmoothingEnabled = true;
        ctx.imageSmoothingQuality = "high";
        ctx.drawImage(img, 0, 0, width, height);

        // Ekspor ke JPEG Blob dengan kualitas yang ditentukan
        canvas.toBlob(
          (blob) => {
            if (!blob) {
              return resolve(file);
            }

            // Jika hasil kompresi ternyata lebih besar dari file asli, gunakan file asli
            if (blob.size >= file.size) {
              return resolve(file);
            }

            const cleanName = file.name.replace(/\.[^/.]+$/, "") + ".jpg";
            const compressedFile = new File([blob], cleanName, {
              type: "image/jpeg",
              lastModified: Date.now(),
            });

            resolve(compressedFile);
          },
          "image/jpeg",
          config.quality
        );
      };

      img.onerror = () => resolve(file);
      img.src = e.target.result;
    };

    reader.onerror = () => resolve(file);
    reader.readAsDataURL(file);
  });
}
