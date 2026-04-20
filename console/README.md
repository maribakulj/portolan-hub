# portolan-console

SvelteKit web console for Portolan Hub. Placeholder only in Sprint 0.

## Local dev

```bash
cd console
npm install
npm run dev
```

The dev server listens on `http://localhost:3000` and reads the API base
URL from `PUBLIC_API_BASE_URL` (default: `http://localhost:8000`).

## Roadmap

- **Sprint 0** (this sprint): placeholder landing page that pings `/health`.
- **Sprint 5**: source explorer, query composer, results grid, IIIF viewer.
- **Sprint 6**: low-code connector editor.
- **Sprint 7**: health dashboard + rights filter + exports.
