# Squidfall docs — the "blank pages," filled in

The upstream Squidfall site (`pages.cdso.army.mil/ai2c/squidfall/docs`) ships these
section **Setup** pages as empty stubs (`Step 1. Text goes here.`). These are our
completed versions, written from the CI/CD pipeline we actually built and verified.

For the system design, see [`../ARCHITECTURE.md`](../ARCHITECTURE.md).

| Section | Page |
|---|---|
| Platform Resources | [setup](platform-resources/setup.md) — the local resources everything runs on |
| Continuous Integration | [setup](continuous-integration/setup.md) — `ci.yml` on the self-hosted runner |
| Continuous Delivery | [setup](continuous-delivery/setup.md) — registry + prod-like deploy |
| Deployment | [setup](deployment/setup.md) — one-shot bootstrap + prod-like release |
| Documentation | [setup](documentation/setup.md) — how these docs are maintained |

**Fastest path (Linux / WSL):** clone the repo, then run `./squidfall.sh`.
