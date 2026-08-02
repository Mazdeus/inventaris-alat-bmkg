import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "sonner";
import App from "./App";
import "./index.css";

/**
 * QueryClient untuk TanStack Query.
 * - retry: hanya 1 kali jika gagal
 * - staleTime: 30 detik — data dianggap fresh selama 30 detik
 * - refetchOnWindowFocus: false — tidak refetch saat user kembali ke tab
 */
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      staleTime: 30_000,
      refetchOnWindowFocus: false,
    },
  },
});

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <App />
      </BrowserRouter>
      <Toaster position="bottom-right" richColors duration={3000} />
    </QueryClientProvider>
  </React.StrictMode>
);
