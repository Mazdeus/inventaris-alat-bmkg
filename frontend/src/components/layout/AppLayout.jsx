import { useState } from "react";
import { Outlet } from "react-router-dom";
import Sidebar from "./Sidebar";
import Header from "./Header";
import { SIDEBAR_COLLAPSED_WIDTH, SIDEBAR_EXPANDED_WIDTH } from "@/lib/constants";

/**
 * Layout utama aplikasi setelah login.
 * Struktur: Sidebar (fixed kiri) + Header (atas) + Konten (Outlet).
 *
 * Menggunakan React Router <Outlet /> — halaman anak dirender di area konten.
 * State `collapsed` mengontrol lebar sidebar dan margin kiri konten.
 */
export default function AppLayout() {
  const [collapsed, setCollapsed] = useState(false);
  const sidebarWidth = collapsed ? SIDEBAR_COLLAPSED_WIDTH : SIDEBAR_EXPANDED_WIDTH;

  return (
    <div className="flex h-screen overflow-hidden bg-gray-50">
      {/* Sidebar */}
      <Sidebar collapsed={collapsed} onToggle={() => setCollapsed(!collapsed)} />

      {/* Area utama */}
      <div
        className="flex flex-1 flex-col overflow-hidden transition-all duration-300"
        style={{ marginLeft: sidebarWidth }}
      >
        <Header collapsed={collapsed} onToggle={() => setCollapsed(!collapsed)} />

        {/* Konten halaman — dirender dari <Outlet /> */}
        <main className="flex-1 overflow-y-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
