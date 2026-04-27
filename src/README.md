# Source Layout

Application code is split by runtime and then by atomic feature.

```text
src/
  backend/
    app/features/<feature>/
    app/shared/
    tests/
  frontend/
    src/features/<feature>/
    src/shared/
```

## Backend Feature Rule

Each backend feature should own its route, schemas, service logic, and tests.

```text
src/backend/app/features/<feature>/
  router.py
  schemas.py
  service.py
src/backend/tests/test_<feature>.py
```

Unit tests are mandatory for every backend feature or behavior change.

Backend shared code belongs under `src/backend/app/shared/` only when multiple feature slices use it. Add backend tests that cover shared behavior directly or through the feature contract.

## Frontend Feature Rule

Each frontend feature should own its component, feature-specific state, and tests.

```text
src/frontend/src/features/<feature>/
  <FeatureComponent>.tsx
  <FeatureComponent>.test.tsx
```

Unit tests are mandatory for every frontend feature or behavior change.

Frontend shared API clients and cross-feature types belong under `src/frontend/src/shared/`. Add colocated tests such as `src/frontend/src/shared/<module>.test.ts` when shared behavior includes mapping, validation, or request construction.
