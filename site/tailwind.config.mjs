/** @type {import('tailwindcss').Config} */
export default {
  content: ["./src/**/*.{astro,html,js,jsx,ts,tsx}"] ,
  theme: {
    extend: {
      colors: {
        ink: {
          950: "#0b142e",
          900: "#111f3d",
          800: "#182950",
        },
        accent: {
          500: "#1f8ef1",
          600: "#1876cc",
        },
        gold: {
          500: "#d4af37",
        },
      },
      fontFamily: {
        sans: ["IBM Plex Sans", "Noto Sans SC", "sans-serif"],
        display: ["IBM Plex Serif", "Noto Serif SC", "serif"],
      },
      boxShadow: {
        soft: "0 10px 30px rgba(15, 28, 63, 0.12)",
      },
    },
  },
  plugins: [],
};
