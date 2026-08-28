/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#eff6ff',
          100: '#dbeafe',
          200: '#bfdbfe',
          300: '#93c5fd',
          400: '#60a5fa',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
          800: '#1e40af',
          900: '#1e3a8a',
        },
        // CANONICAL brand palette — "Option A", decided 2026-08-09 (Stephen).
        // Matches :root vars in src/styles/index.css (keep in sync) and
        // BRAND-GUIDELINES.md. The retired pilot palette (#2B8C96/#D4882B)
        // must not reappear. Use these named colors, never raw hex literals.
        // Values are NOT duplicated here any more. They resolve from the
        // generated contract file src/styles/brand-tokens.css
        // (source of record: design-system/tokens/tokens.json, theme "muni").
        // rgb(var(--x) / <alpha-value>) keeps opacity modifiers working,
        // e.g. border-muni-teal/30.
        muni: {
          navy: 'rgb(var(--brand-primary-rgb) / <alpha-value>)',
          teal: 'rgb(var(--brand-accent-rgb) / <alpha-value>)',
          orange: 'rgb(var(--brand-cta-rgb) / <alpha-value>)',
          gold: 'rgb(var(--brand-gold-rgb) / <alpha-value>)',
        }
      },
    },
  },
  plugins: [],
}
