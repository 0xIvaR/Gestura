/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './index.html',
    './src/**/*.{ts,tsx,js,jsx}'
  ],
  theme: {
    extend: {
      colors: {
        text: {
          primary: '#1A1A1A',
          secondary: '#4A4A4A',
          muted: '#6B6B6B'
        },
        interactive: {
          primary: '#7FCDBB',
          statusbar: '#ADD8E6'
        },
        brand: {
          cyan: '#00D4FF',
          yellow: '#FFE066',
          coral: '#FF6B6B'
        }
      },
      fontFamily: {
        sans: [
          '-apple-system',
          'BlinkMacSystemFont',
          'SF Pro Display',
          'Inter',
          'sans-serif'
        ]
      },
      boxShadow: {
        glass: '0 8px 32px rgba(0, 0, 0, 0.08)',
        brand: '0 4px 16px rgba(127, 205, 187, 0.2)'
      },
      borderRadius: {
        card: '24px',
        statusbar: '30px'
      },
      transitionTimingFunction: {
        brand: 'cubic-bezier(0.4, 0, 0.2, 1)'
      }
    }
  },
  plugins: []
};



