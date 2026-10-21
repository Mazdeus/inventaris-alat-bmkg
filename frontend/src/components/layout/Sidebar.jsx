import { useState } from "react";
import { NavLink, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import {
  LayoutDashboard, Boxes, Users, ArrowLeftRight,
  RotateCcw, Wrench, UserCog, ScrollText,
  ChevronLeft, ChevronRight, CloudLightning, LogOut, LogIn,
  ClipboardList, ChevronDown, List, Send, Building2, Activity,
} from "lucide-react";
import { cn } from "@/lib/utils";

// URL aplikasi Station Quality Monitoring (Proyek A) dari environment variable
const MONITORING_STATION_URL =
  import.meta.env.VITE_MONITORING_STATION_URL ||
  import.meta.env.VITE_STATION_QUALITY_URL ||
  "";

/** Definisi semua menu navigasi sidebar */
const MENU_ITEMS = [
  {
    label: "Dasbor",
    path: "/",
    icon: LayoutDashboard,
    roles: ["Admin", "User"],
  },
  {
    label: "Unit Inventaris",
    path: "/inventory/components",
    icon: Boxes,
    roles: ["Admin", "User"],
  },
  {
    label: "Daftar Barang",
    path: "/inventory/items",
    icon: List,
    roles: ["Admin", "User"],
  },
  {
    label: "Petugas",
    path: "/officers",
    icon: ClipboardList,
    roles: ["Admin"],
  },
  {
    label: "Peminjam",
    path: "/borrowers",
    icon: Users,
    roles: ["Admin"],
  },
  {
    label: "UPT",
    path: "/upts",
    icon: Building2,
    roles: ["Admin"],
    dividerAfter: true,
  },
  {
    label: "Peminjaman",
    path: "/borrow/transactions",
    icon: ArrowLeftRight,
    roles: ["Admin", "User"],
  },
  {
    label: "Pengembalian",
    path: "/returns",
    icon: RotateCcw,
    roles: ["Admin", "User"],
  },
  {
    label: "Pemeliharaan",
    path: "/maintenance",
    icon: Wrench,
    roles: ["Admin", "User"],
    dividerAfter: true,
  },
  {
    label: "Pelimpahan",
    path: "/handovers",
    icon: Send,
    roles: ["Admin", "User"],
  },
  {
    label: "Akun Admin",
    path: "/users",
    icon: UserCog,
    roles: ["Admin"],
  },
  {
    label: "Log Aktivitas",
    path: "/activity-logs",
    icon: ScrollText,
    roles: ["Admin"],
  },
];

// Tambahkan menu Monitoring Station jika URL dikonfigurasi di environment variable
if (
  MONITORING_STATION_URL &&
  !MENU_ITEMS.some((item) => item.label === "Monitoring Station")
) {
  MENU_ITEMS.push({
    label: "Monitoring Station",
    href: MONITORING_STATION_URL,
    icon: Activity,
    roles: ["Admin", "User"],
    dividerBefore: true,
  });
}

/**
 * Sidebar gelap di sisi kiri.
 * Bisa collapse (hanya ikon) atau expand (ikon + label).
 * Menu difilter berdasarkan role user.
 *
 * @param {object} props
 * @param {boolean} props.collapsed - Apakah sidebar sedang collapse
 * @param {function} props.onToggle - Callback untuk toggle collapse/expand
 */
export default function Sidebar({ collapsed, onToggle }) {
  const { user, isAdmin, isAuthenticated, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();

  // Filter menu berdasarkan role
  const visibleMenus = MENU_ITEMS.filter((item) =>
    item.roles.includes(user?.role || "User")
  );

  return (
    <aside
      className={cn(
        "fixed left-0 top-0 z-40 flex h-screen flex-col bg-gray-800 text-gray-300 transition-all duration-300",
        collapsed ? "w-16" : "w-60"
      )}
    >
      {/* Logo area */}
      <div className="flex h-16 items-center border-b border-gray-700 px-3">
        <div className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-lg bg-gray-700">
          <CloudLightning className="h-5 w-5 text-white" />
        </div>
        {!collapsed && (
          <div className="ml-3 overflow-hidden">
            <p className="text-sm font-bold text-white leading-tight">BMKG</p>
            <p className="text-[10px] text-gray-400 leading-tight">Inventaris</p>
          </div>
        )}
        <button
          onClick={onToggle}
          className={cn(
            "ml-auto rounded-md p-1 text-gray-400 hover:bg-gray-700 hover:text-white transition",
            collapsed && "mx-auto mt-4"
          )}
        >
          {collapsed ? (
            <ChevronRight className="h-4 w-4" />
          ) : (
            <ChevronLeft className="h-4 w-4" />
          )}
        </button>
      </div>

      {/* Menu items */}
      <nav className="flex-1 overflow-y-auto scrollbar-hide py-3">
        <ul className="space-y-2 px-2">
          {visibleMenus.map((item, idx) => {
            const isActive = item.path ? location.pathname === item.path : false;
            return (
              <li key={item.path || item.href || item.label}>
                {((item.dividerAfter && idx > 0) || item.dividerBefore) && !collapsed && (
                  <div className="my-2 border-t border-gray-700" />
                )}
                {item.href ? (
                  <a
                    href={item.href}
                    target={item.target || "_blank"}
                    rel="noopener noreferrer"
                    className={cn(
                      "flex items-center rounded-lg px-3 py-2 text-[15px] transition-colors text-gray-300 hover:bg-gray-700 hover:text-white"
                    )}
                    title={collapsed ? item.label : undefined}
                  >
                    <item.icon className="h-[22px] w-[22px] flex-shrink-0" />
                    {!collapsed && <span className="ml-3 truncate">{item.label}</span>}
                  </a>
                ) : (
                  <NavLink
                    to={item.path}
                    className={cn(
                      "flex items-center rounded-lg px-3 py-2 text-[15px] transition-colors",
                      isActive
                        ? "bg-gray-700 text-white"
                        : "text-gray-300 hover:bg-gray-700 hover:text-white"
                    )}
                    title={collapsed ? item.label : undefined}
                  >
                    <item.icon className="h-[22px] w-[22px] flex-shrink-0" />
                    {!collapsed && <span className="ml-3 truncate">{item.label}</span>}
                    {isActive && !collapsed && (
                      <span className="ml-auto h-2 w-2 rounded-full bg-blue-400" />
                    )}
                  </NavLink>
                )}
              </li>
            );
          })}
        </ul>
      </nav>

      {/* Logout / Login area */}
      <div className="border-t border-gray-700 px-2 py-3">
        {isAuthenticated ? (
          <button
            onClick={logout}
            className={cn(
              "flex w-full items-center rounded-lg px-3 py-2 text-[15px] text-gray-400 transition hover:bg-red-600 hover:text-white",
              collapsed && "justify-center"
            )}
            title="Keluar"
          >
            <LogOut className="h-[22px] w-[22px] flex-shrink-0" />
            {!collapsed && <span className="ml-3">Keluar</span>}
          </button>
        ) : (
          <button
            onClick={() => navigate("/login")}
            className={cn(
              "flex w-full items-center rounded-lg px-3 py-2 text-[15px] text-gray-400 transition hover:bg-emerald-600 hover:text-white",
              collapsed && "justify-center"
            )}
            title="Masuk Admin"
          >
            <LogIn className="h-[22px] w-[22px] flex-shrink-0" />
            {!collapsed && <span className="ml-3">Masuk</span>}
          </button>
        )}
      </div>
    </aside>
  );
}
