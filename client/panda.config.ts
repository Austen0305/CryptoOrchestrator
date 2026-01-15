// @ts-nocheck
import { defineConfig } from "@pandacss/dev"

export default defineConfig({
  // Whether to use css reset
  preflight: true,

  // Where to look for your css declarations
  include: ["./src/**/*.{js,jsx,ts,tsx}"],

  // Files to exclude
  exclude: [],

  // Useful for theme customization
  theme: {
    extend: {
      tokens: {
        colors: {
          primary: { value: '#0F172A' },
          secondary: { value: '#334155' },
          accent: { value: '#38BDF8' },
        },
        fonts: {
          heading: { value: 'Inter, sans-serif' },
          body: { value: 'Inter, sans-serif' },
        }
      }
    }
  },

  // The output directory for your css system
  outdir: "styled-system",
})
