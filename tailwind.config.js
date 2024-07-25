module.exports = {
  // ... other config
  theme: {
    extend: {
      colors: {
        gray: {
          750: '#2d333b',
          850: '#22272e',
        },
      },
    },
  },
  plugins: [
    function ({ addUtilities }) {
      const newUtilities = {
        '.text-shadow': {
          textShadow: '0 1px 2px rgba(0, 0, 0, 0.2)',
        },
      };
      addUtilities(newUtilities, ['responsive', 'hover']);
    },
  ],
  // ... other config
};