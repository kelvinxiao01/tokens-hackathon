# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository layout

Two sibling projects, no shared tooling at the root:

- [tokens-be/](tokens-be/) — Python 3.13 backend (currently a stub `main.py`). Managed with `uv` (see `.python-version` and PEP 621 `pyproject.toml` with empty `dependencies`).
- [tokens-fe/](tokens-fe/) — Next.js 16 + React 19 frontend (App Router, Tailwind v4, TypeScript strict).

Run commands from the relevant subdirectory.

## Frontend (`tokens-fe`)

```bash
npm run dev      # next dev — http://localhost:3000
npm run build    # next build
npm run start    # next start (after build)
npm run lint     # eslint (flat config: eslint.config.mjs)
```

**Critical:** this is Next.js 16.2.6 — see [tokens-fe/AGENTS.md](tokens-fe/AGENTS.md). APIs, conventions, and file structure differ from older Next versions you may know. Before writing Next code, read the relevant guide in [tokens-fe/node_modules/next/dist/docs/](tokens-fe/node_modules/next/dist/docs/) (organized as `01-app`, `02-pages`, `03-architecture`, `04-community`) and heed deprecation notices. Do not rely on training-data recall for Next.js APIs here.

Path alias `@/*` maps to the `tokens-fe/` root (see [tokens-fe/tsconfig.json](tokens-fe/tsconfig.json)).

Styling is Tailwind v4 via `@tailwindcss/postcss` (no `tailwind.config.*` — v4 is CSS-first; configure in [tokens-fe/app/globals.css](tokens-fe/app/globals.css)).

## Backend (`tokens-be`)

```bash
uv run main.py   # run the entrypoint
uv sync          # install/refresh deps from pyproject.toml + uv.lock
uv add <pkg>     # add a dependency
```

Requires Python 3.13 (pinned in `.python-version`). No tests, lint, or framework scaffolding yet — add them deliberately when needed rather than assuming a stack.
