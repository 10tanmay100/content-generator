import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        canvas: "#0A0D18",
        surface: "#12162A",
        surface2: "#191E38",
        edge: "#262C4A",
        ink: "#F3F4F8",
        muted: "#9098B8",
        // One signature hue per agent — used consistently across the hero
        // relay, the progress tracker, and result sections so the same
        // color always means the same stage of the pipeline.
        agent: {
          research: "#4FD8E8",
          writing: "#9B87F6",
          editing: "#F6B94D",
          seo: "#46E0A0",
          image: "#F773B8",
          social: "#5B9DF9",
        },
      },
      fontFamily: {
        display: ["var(--font-display)", "sans-serif"],
        body: ["var(--font-body)", "sans-serif"],
      },
    },
  },
  plugins: [],
};

export default config;
