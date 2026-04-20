<script lang="ts">
  import { onMount } from "svelte";

  const apiBase = import.meta.env.PUBLIC_API_BASE_URL ?? "http://localhost:8000";

  type Status = "loading" | "ok" | "error";
  let status: Status = "loading";
  let version = "";
  let errorMessage = "";

  onMount(async () => {
    try {
      const [healthResp, versionResp] = await Promise.all([
        fetch(`${apiBase}/health`),
        fetch(`${apiBase}/version`),
      ]);
      if (!healthResp.ok || !versionResp.ok) {
        throw new Error(`API returned ${healthResp.status} / ${versionResp.status}`);
      }
      const versionBody = await versionResp.json();
      version = versionBody.version;
      status = "ok";
    } catch (err) {
      errorMessage = err instanceof Error ? err.message : String(err);
      status = "error";
    }
  });
</script>

<section>
  <h2>Sprint 0</h2>
  <p>
    This placeholder console is part of the Sprint 0 foundations. It checks that the API is
    reachable and reports its version. The real interface (source explorer, query composer, IIIF
    viewer) lands in Sprint 5.
  </p>

  <div class="status" data-status={status}>
    {#if status === "loading"}
      <span class="dot" /> Contacting API at <code>{apiBase}</code>…
    {:else if status === "ok"}
      <span class="dot ok" /> API reachable — version <code>{version}</code>.
    {:else}
      <span class="dot err" /> API unreachable: {errorMessage}
    {/if}
  </div>

  <ul class="links">
    <li><a href="{apiBase}/docs" target="_blank" rel="noreferrer">API docs (Swagger)</a></li>
    <li><a href="{apiBase}/redoc" target="_blank" rel="noreferrer">API docs (ReDoc)</a></li>
    <li><a href="{apiBase}/openapi.json" target="_blank" rel="noreferrer">OpenAPI schema</a></li>
  </ul>
</section>

<style>
  section {
    line-height: 1.55;
  }
  h2 {
    font-size: 1.1rem;
    margin-bottom: 0.5rem;
  }
  .status {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.75rem 1rem;
    background: var(--bg-elev);
    border-radius: var(--radius);
    margin: 1rem 0;
  }
  .dot {
    width: 0.6rem;
    height: 0.6rem;
    border-radius: 50%;
    background: var(--fg-muted);
  }
  .dot.ok {
    background: var(--ok);
  }
  .dot.err {
    background: var(--err);
  }
  .links {
    list-style: none;
    padding: 0;
    display: flex;
    gap: 1rem;
    flex-wrap: wrap;
  }
</style>
