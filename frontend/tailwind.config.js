/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        bmkg: {
          primary: "#1e293b",
          sidebar: "#0f172a",
          accent: "#3b82f6",
        },
      },
    },
  },
  plugins: [],
};
