import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        mono: ["JetBrains Mono", "Fira Code", "monospace"],
      },
      colors: {
        synapse: {
          bg:       "#0a0a0f",
          surface:  "#111118",
          border:   "#1e1e2e",
          node:     "#16161f",
          idle:     "#3b3b52",
          transmit: "#6366f1",
          pass:     "#22c55e",
          fail:     "#f59e0b",
          error:    "#ef4444",
          text:     "#e2e2f0",
          muted:    "#6b6b8a",
        },
      },
      animation: {
        "pulse-slow": "pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        glow: "glow 2s ease-in-out infinite alternate",
      },
      keyframes: {
        glow: {
          "0%":   { boxShadow: "0 0 4px 1px rgba(99,102,241,0.3)" },
          "100%": { boxShadow: "0 0 12px 3px rgba(99,102,241,0.6)" },
        },
      },
    },
  },
  plugins: [],
};

export default config;
