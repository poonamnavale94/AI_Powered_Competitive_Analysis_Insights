/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}", // Make sure it covers your Dashboard.js
  ],
  theme: {
    extend: {
      colors: {
        primary: '#4A90E2',    // match your website
        secondary: '#D1E8FF',
      },
      fontFamily: {
        sans: ['Helvetica', 'Arial', 'sans-serif'],
      },
    },
  },
  plugins: [],
};
