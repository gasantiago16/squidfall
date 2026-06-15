# Documentation — Setup

How Squidfall's documentation is organized and kept current.

## Sources
- [`../../ARCHITECTURE.md`](../../ARCHITECTURE.md) — full system design, data flow,
  decisions, and the bug log (the source of truth).
- `../../architecture.html` — the same content, self-contained with a system
  diagram; opens in any browser, no internet needed.
- [`../../README.md`](../../README.md) — quick start + current status.
- `docs/` — these section **Setup** pages (Platform Resources, CI, CD, Deployment,
  Documentation), mirroring the upstream site's structure.

## Keeping it current
Docs are updated at every **phase boundary**: the status banners and roadmap tables
in `ARCHITECTURE.md` / `architecture.html` / `README.md` are bumped and committed
alongside the code, so the repo always describes the running system.

## Optional: publish like the upstream site (MkDocs)
The upstream Squidfall site is built with **MkDocs** (Read the Docs theme). To
publish these pages the same way:

```
pip install mkdocs
# add a mkdocs.yml whose nav points at docs/*.md, then:
mkdocs serve     # local preview at http://localhost:8000
mkdocs build     # static site in ./site/
```

Example `mkdocs.yml` nav:

```yaml
site_name: squidfall
nav:
  - Platform Resources: { Setup: platform-resources/setup.md }
  - Continuous Integration: { Setup: continuous-integration/setup.md }
  - Continuous Delivery: { Setup: continuous-delivery/setup.md }
  - Deployment: { Setup: deployment/setup.md }
  - Documentation: { Setup: documentation/setup.md }
```
