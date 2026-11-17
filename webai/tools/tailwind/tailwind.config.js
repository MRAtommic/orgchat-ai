// Tailwind build config — mirrors the inline `tailwind.config` that templates/index.html used with the CDN.
// Build:  see tools/tailwind/README.md
module.exports = {
  darkMode: 'class',
  content: [
    '../../templates/index.html',
    '../../static/js/**/*.js',
  ],
  // classes assembled at runtime (e.g. `bg-${c}-500`) cannot be detected by scanning; add them here if any show up unstyled
  safelist: ['text-amber-500', 'text-rose-600', 'text-emerald-600', 'text-blue-600'],
  theme: {
    extend: {
      colors: {
        brand: { 50: '#eff6ff', 100: '#e0ebff', 200: '#bfdbfe', 300: '#93c5fd', 400: '#60a5fa', 500: '#3b82f6', 600: '#2563eb', 700: '#1d4ed8', 800: '#1e40af', 900: '#1e3a8a', 950: '#0b132b' },
        surface: { 50: '#f8fafc', 100: '#f1f5f9', 200: '#e2e8f0', 300: '#cbd5e1', 400: '#94a3b8', 500: '#64748b', 600: '#475569', 700: '#334155', 750: '#273449', 800: '#1e293b', 850: '#151f32', 900: '#0f172a', 950: '#090d16' },
      },
      fontFamily: { sans: ['Prompt', 'Anuphan', 'IBM Plex Sans Thai', 'Inter', 'sans-serif'] },
    },
  },
};
