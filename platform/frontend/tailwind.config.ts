import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: "#0d1117",
        "bg-raised": "#161b22",
        surface: "#1c2128",
        "surface-hover": "#21262d",
        border: "#30363d",
        "border-subtle": "#21262d",
        text: "#e6edf3",
        "text-secondary": "#8b949e",
        "text-muted": "#6e7681",
        accent: "#58a6ff",
        "accent-muted": "#1f6feb",
        green: "#3fb950",
        "green-muted": "#238636",
        red: "#f85149",
        yellow: "#d29922",
        gold: "#c9a84c",
      },
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui"],
        mono: ["JetBrains Mono", "ui-monospace", "Consolas", "monospace"],
      },
      borderRadius: {
        DEFAULT: "6px",
      },
    },
  },
};

export default config;
