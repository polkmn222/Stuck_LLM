# Backend

FastAPI backend for the conversational stock-analysis agent.

## Commands

```bash
PYTHONPATH=src/backend python3 -m pytest src/backend/tests -q
PYTHONPATH=src/backend uvicorn app.main:app --host 127.0.0.1 --port 8000
```

## Feature Layout

- `app/features/<feature>/router.py`: HTTP routes for one atomic feature.
- `app/features/<feature>/schemas.py`: request/response contracts.
- `tests/test_<feature>.py`: behavior tests for one feature.
