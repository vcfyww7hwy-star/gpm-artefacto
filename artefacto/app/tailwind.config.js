import animate from "tailwindcss-animate";

/**
 * Color de Tailwind ligado a un token CSS. Sin modificador de opacidad emite
 * `var(--token)`; con `/NN` (p. ej. `bg-accent/10`) emite `color-mix()` para
 * que los modificadores funcionen aunque el token sea un hex/rgba opaco.
 * Las utilidades legacy `bg-opacity-*` (opacityValue = var(--tw-*)) se ignoran.
 */
const token = (name) => ({ opacityValue }) => {
  if (opacityValue === undefined || opacityValue === "1" || String(opacityValue).startsWith("var(")) {
    return `var(${name})`;
  }
  const pct = Math.round(Number(opacityValue) * 1000) / 10;
  return `color-mix(in srgb, var(${name}) ${pct}%, transparent)`;
};

/** @type {import('tailwindcss').Config} */
export default {
  darkMode: [
    "variant",
    [
      '@media (prefers-color-scheme: dark) { &:not([data-theme="light"] *) }',
      '&:is([data-theme="dark"] *)',
    ],
  ],
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        /* --- tokens propios (nombres = variables CSS) --------------------- */
        bg: token("--bg"),
        surface: {
          DEFAULT: token("--surface"),
          2: token("--surface-2"),
          hover: token("--surface-hover"),
        },
        hairline: token("--hairline"),
        ink: {
          DEFAULT: token("--ink"),
          2: token("--ink-2"),
          3: token("--ink-3"),
        },
        accent: {
          DEFAULT: token("--accent"),
          soft: "var(--accent-soft)",
          foreground: token("--on-accent"),
        },
        ok: token("--ok"),
        warn: {
          text: token("--warn-text"),
          fill: token("--warn-fill"),
        },
        risk: token("--risk"),
        info: token("--info"),
        c: {
          conservador: token("--c-conservador"),
          base: token("--c-base"),
          favorable: token("--c-favorable"),
        },
        cat: {
          1: token("--cat-1"),
          2: token("--cat-2"),
          3: token("--cat-3"),
        },
        /* --- sistema shadcn/ui (mapeado a los tokens en src/index.css) ---- */
        border: token("--border"),
        input: token("--input"),
        ring: token("--ring"),
        background: token("--background"),
        foreground: token("--foreground"),
        primary: {
          DEFAULT: token("--primary"),
          foreground: token("--primary-foreground"),
        },
        secondary: {
          DEFAULT: token("--secondary"),
          foreground: token("--secondary-foreground"),
        },
        destructive: {
          DEFAULT: token("--destructive"),
          foreground: token("--destructive-foreground"),
        },
        muted: {
          DEFAULT: token("--muted"),
          foreground: token("--muted-foreground"),
        },
        popover: {
          DEFAULT: token("--popover"),
          foreground: token("--popover-foreground"),
        },
        card: {
          DEFAULT: token("--card"),
          foreground: token("--card-foreground"),
        },
      },
      fontFamily: {
        sans: ["var(--font-sans)"],
        serif: ["var(--font-serif)"],
        mono: ["var(--font-mono)"],
      },
      borderRadius: {
        1: "var(--radius-1)",
        2: "var(--radius-2)",
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
      boxShadow: {
        1: "var(--shadow-1)",
      },
      keyframes: {
        "accordion-down": {
          from: { height: "0" },
          to: { height: "var(--radix-accordion-content-height)" },
        },
        "accordion-up": {
          from: { height: "var(--radix-accordion-content-height)" },
          to: { height: "0" },
        },
      },
      animation: {
        "accordion-down": "accordion-down 0.2s ease-out",
        "accordion-up": "accordion-up 0.2s ease-out",
      },
    },
  },
  plugins: [animate],
};
