# Stock Analysis Agent

Conversational stock-analysis agent scaffold.

## Run Locally

Start backend and frontend together from the repository root:

```bash
./run-all.sh
```

Default URLs:

- Frontend: `http://127.0.0.1:5174`
- Backend: `http://127.0.0.1:8010`
- Backend through frontend proxy: `http://127.0.0.1:5174/api/health`

Override ports when needed:

```bash
BACKEND_PORT=8020 FRONTEND_PORT=5180 ./run-all.sh
```

## Hosted-Mode Guard

Local development remains unauthenticated by default. To require an API key for non-health backend requests:

```bash
STUCK_LLM_REQUIRE_API_KEY=true STUCK_LLM_API_KEY=change-me ./run-all.sh
```

Clients can pass the key as `Authorization: Bearer <key>` or `X-Stuck-LLM-API-Key: <key>`.

Allowed browser origins default to the local Vite hosts. Override them with:

```bash
STUCK_LLM_CORS_ORIGINS=http://127.0.0.1:5174,http://localhost:5174 ./run-all.sh
```

## Source Layout

- Backend: `src/backend`
- Frontend: `src/frontend`
- Feature conventions: `src/README.md`

## Local MVP State

The backend stores development settings and conversations in `.local/stuck_llm_state.json` by default. Override it with:

```bash
STUCK_LLM_STATE_PATH=/tmp/stuck_llm_state.json ./run-all.sh
```

## MVP API

- `GET /health`
- `GET /settings`
- `PATCH /settings`
- `POST /conversations`
- `GET /conversations/{conversation_id}`
- `POST /conversations/{conversation_id}/messages`
- `POST /ingestion/collect`
- `POST /analysis/requests`
- `POST /scoring/evaluate`
- `POST /backtests/simulations`
- `GET /market-data/quotes/{market}/{symbol}`

The frontend uses the Vite proxy, so browser calls go through `/api/*`.
