# FIFA WC 2026 Frontend (Phase 0)

Production-grade frontend foundation for the FIFA World Cup 2026 Intelligence & Prediction Platform.

## Stack

- React + Vite + TypeScript
- TailwindCSS v4
- Framer Motion
- Zustand
- React Router DOM
- shadcn/ui-ready configuration

## Local Development

1. Install dependencies

```bash
npm install
```

2. Start development server

```bash
npm run dev
```

3. Quality checks

```bash
npm run lint
npm run typecheck
npm run format
```

## Structure

```text
src/
  assets/
  components/
  features/
  hooks/
  layouts/
  lib/
  pages/
  providers/
  routes/
  services/
  store/
  styles/
  types/
```

## Design System

- Light premium FIFA-style visual language
- Single-theme setup (no dark mode, no theme switching)
- Global tokens in `src/styles/globals.css`:
  - color palette
  - typography
  - spacing
  - shadows
  - radii
  - breakpoints

## Routing

- Central route constants in `src/routes/constants.ts`
- Nested layout routing in `src/routes/index.tsx`
- Protected route preparation in `src/routes/ProtectedRoute.tsx`

## Notes

This phase intentionally excludes analytics logic, simulation engines, and ML prediction implementation. The goal is scalable architecture and production-ready foundations.
