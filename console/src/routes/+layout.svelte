<script lang="ts">
  import "../app.css";
</script>

<main>
  <header>
    <h1>Portolan Hub</h1>
    <p class="tagline">Unified query layer for distributed heritage data.</p>
  </header>
  <slot />
</main>

<style>
  main {
    max-width: 960px;
    margin: 0 auto;
    padding: 2rem 1.5rem;
  }
  header {
    margin-bottom: 2rem;
    border-bottom: 1px solid var(--bg-elev);
    padding-bottom: 1rem;
  }
  h1 {
    margin: 0;
    font-size: 1.5rem;
    letter-spacing: 0.02em;
  }
  .tagline {
    margin: 0.25rem 0 0;
    color: var(--fg-muted);
    font-size: 0.9rem;
  }
</style>
