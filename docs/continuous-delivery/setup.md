# Continuous Delivery — Setup

CD builds, versions, deploys, and health-gates a **prod-like** stack on a release
tag. Workflow: `.github/workflows/cd.yml`; topology: `compose.prod.yml`.

## Step 1. Local registry
Start it (see [Platform Resources — Setup](../platform-resources/setup.md) §4).
CD pushes images as `localhost:5000/squidfall/<service>:<sha>`.

## Step 2. Add `compose.prod.yml`
A separate `squidfall-prod` project that runs **alongside** dev:
- images pulled from `localhost:5000` (`TAG` selects the version),
- distinct container names (`squidfall-prod-*`),
- shifted host ports (`:8080 / :18000 / :18001 / :18002 / :15432`),
- its own DB volume,
- **network aliases** (`squidfall-database`, `squidfall-tools`, `squidfall-inference`)
  so the committed `.env` files resolve unchanged inside the prod network.

## Step 3. Add `.github/workflows/cd.yml`
Abridged:

```yaml
on: { push: { tags: ['v*'] }, workflow_dispatch: {} }
jobs:
  cd:
    runs-on: [self-hosted, windows, x64]
    env: { REGISTRY: localhost:5000, TAG: ${{ github.sha }} }
    steps:
      - uses: actions/checkout@v5
      - run: docker compose --profile all build
      - name: Tag + push images by SHA      # docker tag/push each -> $REGISTRY/squidfall/<svc>:$TAG
      - run: docker compose -p squidfall-prod -f compose.prod.yml up -d --pull always
      - name: Health gate                   # curl :18001/api/v1/health, :8080/, :18000/api/v1/chats/ -> 200
      - name: Promote :stable               # retag the pushed images as :stable
      - name: Rollback on failure           # if: failure() -> redeploy with TAG=stable
```

## Step 4. Cut a release

```
git tag v0.1.0 && git push origin v0.1.0
```

CD: build → SHA-tag → push to the registry → deploy `squidfall-prod` →
**health gate** → promote `:stable`. If the health gate fails, it **rolls back**
to the last `:stable`. Prod UI: <http://localhost:8080> (alongside dev on
<http://localhost>). First release shipped: **v0.1.0**.
