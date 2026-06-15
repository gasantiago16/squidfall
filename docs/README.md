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

**On GitLab (e.g. an Army instance):** the GitHub Actions pipeline is translated in
[`../.gitlab-ci.yml`](../.gitlab-ci.yml) for a shell-executor GitLab Runner — same
stages (build · test · lint · Trivy · deploy-on-tag + rollback). See the CI and CD setup pages.
