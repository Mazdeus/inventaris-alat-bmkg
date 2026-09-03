import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { CloudLightning, Eye, EyeOff, Loader2 } from "lucide-react";

/**
 * Schema validasi form login dengan Zod.
 * - username: wajib, min 3 karakter
 * - password: wajib, min 1 karakter (backend yang verifikasi)
 */
const loginSchema = z.object({
  username: z.string().min(1, "Nama pengguna wajib diisi"),
  password: z.string().min(1, "Kata sandi wajib diisi"),
});

/**
 * Halaman login pengguna.
 *
 * Fitur:
 * - Tampilan minimalis dengan logo BMKG dan judul sistem
 * - Form username + password dengan validasi client-side
 * - Toggle show/hide password
 * - Error handling: pesan error dari backend ditampilkan
 * - Loading state saat request sedang berlangsung
 * - Setelah login sukses → redirect ke /
 */
export default function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();

  const [showPassword, setShowPassword] = useState(false);
  const [serverError, setServerError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm({
    resolver: zodResolver(loginSchema),
    defaultValues: { username: "", password: "" },
  });

  /**
   * Handler submit form login.
   * @param {object} data - { username, password } dari form
   */
  const onSubmit = async (data) => {
    setServerError("");
    setSubmitting(true);
    try {
      await login(data.username, data.password);
      navigate("/", { replace: true });
    } catch (err) {
      const msg =
        err.response?.data?.message ||
        err.response?.data?.detail ||
        "Gagal menghubungi server. Pastikan backend berjalan.";
      setServerError(msg);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-100 px-4">
      <div className="w-full max-w-sm rounded-xl bg-white p-8 shadow-lg">
        {/* Logo dan judul */}
        <div className="mb-6 text-center">
          <div className="mx-auto mb-3 flex h-14 w-14 items-center justify-center rounded-full bg-slate-800">
            <CloudLightning className="h-7 w-7 text-white" />
          </div>
          <h1 className="text-lg font-bold text-slate-800">
            Sistem Inventaris Alat
          </h1>
          <p className="text-sm text-slate-500">BMKG</p>

        </div>

        {/* Server error */}
        {serverError && (
          <div className="mb-4 rounded-md bg-red-50 px-4 py-3 text-sm text-red-700 border border-red-200">
            {serverError}
          </div>
        )}

        {/* Form login */}
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          {/* Username */}
          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">
              Nama Pengguna
            </label>
            <input
              type="text"
              autoComplete="username"
              placeholder="Masukkan nama pengguna"
              className={`w-full rounded-md border px-3 py-2 text-sm outline-none transition focus:ring-2 focus:ring-slate-400 ${
                errors.username ? "border-red-400" : "border-gray-300"
              }`}
              {...register("username")}
            />
            {errors.username && (
              <p className="mt-1 text-xs text-red-500">{errors.username.message}</p>
            )}
          </div>

          {/* Password */}
          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">
              Kata Sandi
            </label>
            <div className="relative">
              <input
                type={showPassword ? "text" : "password"}
                autoComplete="current-password"
                placeholder="Masukkan kata sandi"
                className={`w-full rounded-md border px-3 py-2 pr-10 text-sm outline-none transition focus:ring-2 focus:ring-slate-400 ${
                  errors.password ? "border-red-400" : "border-gray-300"
                }`}
                {...register("password")}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                tabIndex={-1}
              >
                {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </button>
            </div>
            {errors.password && (
              <p className="mt-1 text-xs text-red-500">{errors.password.message}</p>
            )}
          </div>

          {/* Submit */}
          <button
            type="submit"
            disabled={submitting}
            className="flex w-full items-center justify-center rounded-md bg-slate-800 px-4 py-2.5 text-sm font-medium text-white transition hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {submitting ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Masuk...
              </>
            ) : (
              "Masuk"
            )}
          </button>
        </form>
      </div>
    </div>
  );
}
