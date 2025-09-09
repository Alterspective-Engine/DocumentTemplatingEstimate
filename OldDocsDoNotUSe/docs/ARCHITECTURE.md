# EstimateDoc Architecture

This document describes the current system architecture, components, and integration points for the EstimateDoc project.

## Overview

- Client: React + TypeScript single-page application (SPA) in `estimatedoc-dashboard/client`.
- Server: Express + TypeScript REST API in `estimatedoc-dashboard/server`.
- Database: PostgreSQL hosting document, field, and template data.
- Data/ETL: SQL scripts and Python utilities at the repo root for import, validation, and reporting.

## Client (SPA)

- Entry: `src/index.tsx` renders `App`.
- Routing: `react-router-dom` provides routes:
  - `/` → Home (index)
  - `/dashboard` → Dashboard
  - `/templates` → Template Browser
  - `/templates/:rowId` → Template Details (evidence)
- Shared Components: `Navigation` (top nav with bidirectional navigation), `StatsCard`, `TemplateTable`, `DataEvidenceModal`.
- API Layer: `src/services/api.ts` wraps REST endpoints with typed interfaces.
- UX: Tailwind utility classes, skeleton placeholders for loading, accessible roles/labels, hover transitions.

## Server (API)

- Entry: `src/index.ts`.
- Routes under `/api`:
  - `GET /api/health` — healthcheck
  - `GET /api/stats/overview` — KPI overview filtered to Excel templates
  - `GET /api/stats/complexity-distribution`
  - `GET /api/stats/matching`
  - `GET /api/stats/field-reusability`
  - `GET /api/stats/complexity-trends`
  - `GET /api/templates` — paginated templates
  - `GET /api/templates/:rowId/details` — detailed evidence
  - `GET /api/templates/browse` — filtered/paginated list (server-side)
  - `GET /api/templates/:rowId/validate` — cross-check calculations

Environment configuration (see `estimatedoc-dashboard/server/.env.example`):

```
PORT=3001
DB_HOST=localhost
DB_PORT=5432
DB_NAME=estimatedoc
DB_USER=estimatedoc_user
DB_PASSWORD=estimatedoc_pass_2024
```

## Database

- Core tables referenced by the API include `excel_templates`, `template_matches`, `documents`, `document_fields`, and `document_complexity`.
- Suggested indexes for performance:
  - `template_matches (excel_row_id)`, `template_matches (document_id)`
  - `document_fields (document_id)`, `document_fields (field_id)`
  - `documents (document_id)`

## Navigation & Integration Rules

- All pages must be reachable from `/` via router-controlled navigation.
- Bidirectional navigation is provided by the navigation bar and browser back support.
- No orphaned files: all React components are imported by pages or the router; legacy standalone HTML is moved under `docs/legacy-ui` for reference and is not part of the application bundle.

## Testing

- Client tests use `react-scripts test` with a minimal smoke test (no network mocks in production code).
- Server tests always use the live PostgreSQL database via environment variables and Supertest.
  - Configure `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` before running `npm test` in `estimatedoc-dashboard/server`.
  - Seed schema with `npm run seed` (optional) using `sql/01_create_schema.sql`.

## Security

- Secrets are not committed. Use environment variables. A sample is provided as `.env.example` in the server package.
- CORS should be restricted in production deployments.

## Deployment

- Build client: `cd estimatedoc-dashboard/client && npm run build`.
- Build server: `cd estimatedoc-dashboard/server && npm run build`.
- Serve the client build via a static host and run the server process separately, or proxy via a reverse proxy.
