/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        canvas: '#ffffff',
        card: '#ffffff',
        brand: {
          lime: '#d9f99d', // Active green/lime pill color
          limeDark: '#4d7c0f',
          peach: '#ffedd5',
          peachBorder: '#fed7aa',
          peachText: '#c2410c',
          purple: '#f3e8ff',
          purpleBorder: '#e9d5ff',
          purpleText: '#7e22ce',
          mint: '#ecfccb',
          mintBorder: '#d9f99d',
          mintText: '#4d7c0f',
          sky: '#e0f2fe',
          skyBorder: '#bae6fd',
          skyText: '#0369a1',
        },
        slate: {
          850: '#151e2e',
          900: '#0f172a',
          950: '#0b0f19'
        }
      },
      fontFamily: {
        sans: ['Plus Jakarta Sans', 'Inter', '-apple-system', 'BlinkMacSystemFont', 'sans-serif'],
      },
      borderRadius: {
        '2.5xl': '1.25rem',
        '3xl': '1.75rem',
        '4xl': '2.25rem',
      },
      boxShadow: {
        'app': '0 20px 40px -15px rgba(0, 0, 0, 0.07), 0 0 0 1px rgba(0, 0, 0, 0.04)',
        'card': '0 4px 12px rgba(0, 0, 0, 0.03), 0 0 0 1px rgba(0, 0, 0, 0.04)',
        'pill': '0 2px 6px rgba(0, 0, 0, 0.04)',
      }
    },
  },
  plugins: [],
}
