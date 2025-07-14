/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/**/*.{js,jsx,ts,tsx}',
    './*.{js,jsx,ts,tsx}',
    './components/**/*.{js,jsx,ts,tsx}',
    './pages/**/*.{js,jsx,ts,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        game: {
          primary: '#1e40af',
          secondary: '#7c3aed',
          success: '#059669',
          warning: '#d97706',
          danger: '#dc2626',
          background: '#1e1e2e',
          surface: '#313244',
          text: '#cdd6f4',
          piece: {
            red: '#f38ba8',
            black: '#585b70',
            gold: '#f9e2af',
            silver: '#a6adc8',
          },
          slot: {
            empty: '#45475a',
            host: '#f9e2af',
            player: '#74c0fc',
            bot: '#cba6f7',
            current: '#a6e3a1',
          },
        },
      },
      fontFamily: {
        game: ['Inter', 'system-ui', 'sans-serif'],
      },
      spacing: {
        18: '4.5rem',
        22: '5.5rem',
        88: '22rem',
        96: '24rem',
      },
      animation: {
        deal: 'deal 0.5s ease-out',
        'piece-select': 'pieceSelect 0.2s ease-out',
        'phase-transition': 'fadeInUp 0.3s ease-out',
        'pulse-glow': 'pulseGlow 2s infinite',
        'slide-in': 'slideIn 0.3s ease-out',
        'bounce-subtle': 'bounceSubtle 0.4s ease-out',
        slideIn: 'slideInDown 0.8s ease-out',
      },
      keyframes: {
        deal: {
          '0%': {
            transform: 'translateY(-100px) rotate(180deg)',
            opacity: '0',
          },
          '50%': {
            transform: 'translateY(-20px) rotate(90deg)',
            opacity: '0.5',
          },
          '100%': { transform: 'translateY(0) rotate(0deg)', opacity: '1' },
        },
        pieceSelect: {
          '0%': { transform: 'scale(1)' },
          '50%': { transform: 'scale(1.1)' },
          '100%': { transform: 'scale(1.05)' },
        },
        fadeInUp: {
          '0%': { transform: 'translateY(20px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        pulseGlow: {
          '0%, 100%': { boxShadow: '0 0 10px rgba(59, 130, 246, 0.5)' },
          '50%': { boxShadow: '0 0 20px rgba(59, 130, 246, 0.8)' },
        },
        slideIn: {
          '0%': { transform: 'translateX(-100%)', opacity: '0' },
          '100%': { transform: 'translateX(0)', opacity: '1' },
        },
        bounceSubtle: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-4px)' },
        },
        slideInDown: {
          from: { opacity: '0', transform: 'translateY(-50px)' },
          to: { opacity: '1', transform: 'translateY(0)' },
        },
      },
      boxShadow: {
        game: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
        'game-lg':
          '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
        piece: '0 2px 8px rgba(0, 0, 0, 0.15)',
        'piece-hover': '0 4px 12px rgba(0, 0, 0, 0.2)',
        glow: '0 0 20px rgba(59, 130, 246, 0.6)',
      },
      gridTemplateColumns: {
        'game-layout': '1fr 2fr 1fr',
        slots: 'repeat(2, 1fr)',
        pieces: 'repeat(auto-fit, minmax(4rem, 1fr))',
      },
      backdropBlur: {
        game: '8px',
      },
    },
  },
  plugins: [],
};
