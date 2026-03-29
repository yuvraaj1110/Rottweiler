/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        midnight: {
          bg: '#050505',
          surface: '#0A1128',
          accent: '#1E3A8A',
          cobalt: '#2563EB',
          slate: '#94A3B8',
        },
      },
      fontFamily: {
        terminal: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}