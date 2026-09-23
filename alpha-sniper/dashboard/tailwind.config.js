/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: { gold: { 400: '#facc15', 500: '#eab308' }, dark: { 900: '#0f172a', 800: '#1e293b' } },
      boxShadow: { 'glow-gold': '0 0 20px rgba(234, 179, 8, 0.3)', 'glow-green': '0 0 20px rgba(34, 197, 94, 0.3)', 'glow-red': '0 0 20px rgba(239, 68, 68, 0.3)' }
    },
  },
  plugins: [],
}
