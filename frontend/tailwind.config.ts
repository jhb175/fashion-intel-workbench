import type { Config } from 'tailwindcss';

const config: Config = {
  content: [
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/lib/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['var(--font-inter)', 'var(--font-noto-sans-sc)', 'system-ui', 'sans-serif'],
      },
      colors: {
        bg: { DEFAULT: '#f8f9fc', card: '#ffffff', hover: '#f1f3f9', active: '#e8ebf4' },
        fg: { DEFAULT: '#1a1a2e', secondary: '#5a5b6a', muted: '#9394a5', light: '#c4c5d0' },
        primary: { DEFAULT: '#4f46e5', hover: '#4338ca', light: '#818cf8', bg: '#eef2ff', text: '#3730a3' },
        border: { DEFAULT: '#e5e7eb', hover: '#d1d5db' },
      },
      screens: { desktop: '1024px' },
      fontSize: { '2xs': ['0.6875rem', '1rem'] },
      boxShadow: {
        card: '0 1px 3px rgba(0,0,0,0.04), 0 1px 2px rgba(0,0,0,0.06)',
        'card-hover': '0 4px 12px rgba(0,0,0,0.08), 0 2px 4px rgba(0,0,0,0.04)',
        panel: '0 8px 30px rgba(0,0,0,0.08)',
      },
    },
  },
  plugins: [],
};
export default config;
