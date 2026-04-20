# Contributing to Portolan Hub

Thanks for considering a contribution. This guide covers the essentials.
Deeper docs live in [`docs/`](docs/).

## Ways to help

Most useful in the early days:

1. **New connectors** — a YAML manifest plus fixtures is usually enough.
   See [`docs/plugins/authoring.md`](docs/plugins/authoring.md) (finalized in Sprint 6).
2. **VCR fixtures** for existing connectors — improve regression coverage.
3. **Console translations** (FR / EN, more welcome).
4. **Real-usage feedback** — open an issue describing what you tried to
   do and where the tool failed you.

Please discuss non-trivial changes in an issue before writing a lot of code.

## Development setup

```bash
git clone https://github.com/maribakulj/portolan-hub.git
cd portolan-hub
cp .env.example .env
uv sync --all-packages --all-extras
make test        # should pass on a fresh checkout
make dev         # full docker-compose stack
```

Node 20 and Docker are required for the console and the integration stack.

## Code quality

- `make lint` — ruff + format check.
- `make typecheck` — mypy strict.
- `make test` — pytest with coverage.

Pre-commit hooks are installed via `pre-commit install`. CI will reject
anything the local hooks let through, so running them locally saves you
a round-trip.

## Branching and PRs

- Default branch: `main`.
- Feature branches: `feature/<short-name>` or `fix/<short-name>`.
- Conventional commits (`feat:`, `fix:`, `docs:`, `refactor:`…). `!` for
  breaking changes.
- One logical change per PR. Stacked PRs are welcome for larger efforts.
- PRs that change the **plugin contract** or the **pivot model** must
  ship with an ADR.

## Tests

- Unit tests live under each package's `tests/`.
- Integration tests use VCR cassettes checked into the repo. Cassettes
  are refreshed on purpose, never silently.
- Property-based tests (hypothesis) are encouraged for the pivot and
  connector output.

## Reporting security issues

Please do not open a public issue for security reports. See
[SECURITY.md](SECURITY.md) (added in Sprint 7) or email the maintainers
directly.

## Code of conduct

See [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).
