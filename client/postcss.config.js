const path = require('path');

module.exports = {
  plugins: {
    tailwindcss: {
      config: path.resolve(__dirname, '..', 'tailwind.config.ts'),
    },
    autoprefixer: {},
  },
  // Explicitly set from option to fix PostCSS warning
  from: undefined, // Will be set by Vite
}
