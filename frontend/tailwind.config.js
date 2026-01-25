/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{vue,js,ts}"],
  theme: {
    extend: {
      colors: {
        bg: "rgb(var(--c-bg) / <alpha-value>)",
        surface: "rgb(var(--c-surface) / <alpha-value>)",
        surface2: "rgb(var(--c-surface-2) / <alpha-value>)",
        text: "rgb(var(--c-text) / <alpha-value>)",
        muted: "rgb(var(--c-text-muted) / <alpha-value>)",
        border: "rgb(var(--c-border) / <alpha-value>)",
        accent: "rgb(var(--c-accent) / <alpha-value>)",
        "on-accent": "rgb(var(--c-on-accent) / <alpha-value>)",
        overlay: "rgb(var(--c-overlay) / <alpha-value>)",
        primary: "rgb(var(--c-bg) / <alpha-value>)",
      },
      boxShadow: {
        float: "var(--shadow-float)",
        card: "var(--shadow-card)",
        inset: "var(--shadow-inset)",
      },
    },
  },
  plugins: [require("tailwindcss-animate")]
};

