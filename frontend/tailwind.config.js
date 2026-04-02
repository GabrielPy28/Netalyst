/** @type {import('tailwindcss').Config} */
export default {
  darkMode: ["class"],
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          purple: "#6641ed",
          blue: "#79bcf7",
          pink: "#ff47ac",
          dark: "#0f172a",
          white: "#F8FAFC",
          green: "#31C950",
          yellow: "#FFDF20",
          red: "#E7180B",
        },
      },
      fontFamily: {
        sans: ["DM Sans", "system-ui", "sans-serif"],
        display: ["Outfit", "system-ui", "sans-serif"],
      },
      boxShadow: {
        glow: "0 0 60px -12px rgba(102, 65, 237, 0.45)",
        card: "0 25px 50px -12px rgba(15, 23, 42, 0.35)",
      },
    },
  },
  plugins: [],
};
