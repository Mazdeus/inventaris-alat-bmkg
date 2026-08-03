import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { format } from "date-fns";
import { id } from "date-fns/locale";
import { Menu, Clock, User, LogOut, LogIn, ChevronDown } from "lucide-react";
import { cn } from "@/lib/utils";
import { getInitials } from "@/lib/formatters";
import { ROLE_LABELS } from "@/lib/constants";

/**
 * Header atas — tombol sidebar toggle, jam live, user dropdown.
 *
 * @param {object} props
 * @param {boolean} props.collapsed - Apakah sidebar collapsed (mempengaruhi tombol toggle)
 * @param {function} props.onToggle - Callback toggle sidebar
 */
export default function Header({ collapsed, onToggle }) {
  const { user, isAuthenticated, logout } = useAuth();
  const navigate = useNavigate();
  const [now, setNow] = useState(new Date());
  const [dropdownOpen, setDropdownOpen] = useState(false);

  // Jam live — update setiap 1 detik
  useEffect(() => {
    const timer = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  const wib = format(now, "HH:mm:ss", { locale: id });
  const utc = format(now, "HH:mm:ss", { locale: id });
  const dateStr = format(now, "EEEE, dd MMMM yyyy", { locale: id });

  return (
    <header className="sticky top-0 z-30 flex h-14 items-center justify-between border-b border-gray-200 bg-white px-4 shadow-sm">
      {/* Kiri: toggle sidebar */}
      <button
        onClick={onToggle}
        className="rounded-md p-1.5 text-slate-500 hover:bg-gray-100 transition"
      >
        <Menu className="h-5 w-5" />
      </button>

      {/* Tengah: jam */}
      <div className="flex items-center gap-4 text-xs text-gray-500">
        <div className="hidden items-center gap-1 sm:flex">
          <Clock className="h-3.5 w-3.5" />
          <span className="font-medium text-gray-700">{wib}</span>
          <span className="text-gray-400">WIB</span>
        </div>
        <span className="hidden text-gray-300 lg:inline">|</span>
        <span className="hidden text-gray-400 lg:inline">{utc} UTC</span>
        <span className="hidden text-gray-500 lg:inline">• {dateStr}</span>
      </div>

      {/* Kanan: user / login */}
      {isAuthenticated ? (
        <div className="relative">
          <button
            onClick={() => setDropdownOpen(!dropdownOpen)}
            className="flex items-center gap-2 rounded-md px-2 py-1 text-sm transition hover:bg-gray-100"
          >
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-slate-700 text-xs font-bold text-white">
              {getInitials(user?.full_name)}
            </div>
            <span className="hidden text-sm font-medium text-slate-700 sm:inline">
              {user?.full_name}
            </span>
            <ChevronDown className="hidden h-3.5 w-3.5 text-gray-400 sm:inline" />
          </button>

          {/* Dropdown */}
          {dropdownOpen && (
            <>
              <div
                className="fixed inset-0 z-20"
                onClick={() => setDropdownOpen(false)}
              />
              <div className="absolute right-0 top-full z-30 mt-1 w-56 rounded-lg border border-gray-200 bg-white py-1 shadow-lg">
                <div className="border-b border-gray-100 px-4 py-2">
                  <p className="text-sm font-medium text-slate-800">
                    {user?.full_name}
                  </p>
                  <p className="text-xs text-gray-500">{ROLE_LABELS[user?.role] || user?.role}</p>
                </div>
                <button
                  onClick={() => {
                    setDropdownOpen(false);
                    logout();
                  }}
                  className="flex w-full items-center gap-2 px-4 py-2 text-sm text-red-600 transition hover:bg-red-50"
                >
                  <LogOut className="h-4 w-4" />
                  Keluar
                </button>
              </div>
            </>
          )}
        </div>
      ) : (
        <button
          onClick={() => navigate("/login")}
          className="flex items-center gap-1.5 rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm text-slate-600 transition hover:bg-slate-50 hover:text-slate-800"
        >
          <LogIn className="h-4 w-4" />
          <span className="hidden sm:inline">Masuk</span>
        </button>
      )}
    </header>
  );
}
