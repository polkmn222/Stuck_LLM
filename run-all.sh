#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$ROOT_DIR/src/backend"
FRONTEND_DIR="$ROOT_DIR/src/frontend"

if [ -f "$ROOT_DIR/.env" ]; then
  set -a
  # shellcheck disable=SC1091
  source "$ROOT_DIR/.env"
  set +a
fi

BACKEND_HOST="${BACKEND_HOST:-127.0.0.1}"
BACKEND_PORT="${BACKEND_PORT:-8010}"
FRONTEND_HOST="${FRONTEND_HOST:-127.0.0.1}"
FRONTEND_PORT="${FRONTEND_PORT:-5174}"
AUTO_OPEN_BROWSER="${AUTO_OPEN_BROWSER:-1}"

BACKEND_URL="http://$BACKEND_HOST:$BACKEND_PORT"
FRONTEND_URL="http://$FRONTEND_HOST:$FRONTEND_PORT"

BACKEND_PID=""
FRONTEND_PID=""

cleanup() {
  if [ -n "$FRONTEND_PID" ] && kill -0 "$FRONTEND_PID" 2>/dev/null; then
    kill "$FRONTEND_PID" 2>/dev/null || true
  fi
  if [ -n "$BACKEND_PID" ] && kill -0 "$BACKEND_PID" 2>/dev/null; then
    kill "$BACKEND_PID" 2>/dev/null || true
  fi
  if [ -n "$FRONTEND_PID" ]; then
    wait "$FRONTEND_PID" 2>/dev/null || true
  fi
  if [ -n "$BACKEND_PID" ]; then
    wait "$BACKEND_PID" 2>/dev/null || true
  fi
}

shutdown() {
  trap - EXIT INT TERM
  cleanup
  exit 130
}

trap cleanup EXIT
trap shutdown INT TERM

open_frontend() {
  local url="$1"

  (
    if command -v curl >/dev/null 2>&1; then
      for _ in {1..30}; do
        if curl -fsS "$url" >/dev/null 2>&1; then
          break
        fi
        sleep 1
      done
    else
      sleep 2
    fi

    if command -v open >/dev/null 2>&1; then
      open "$url" >/dev/null 2>&1 || true
    elif command -v xdg-open >/dev/null 2>&1; then
      xdg-open "$url" >/dev/null 2>&1 || true
    else
      echo "Browser auto-open is unavailable. Open $url manually."
    fi
  ) &
}

if [ ! -d "$FRONTEND_DIR/node_modules" ]; then
  echo "Installing frontend dependencies..."
  (cd "$FRONTEND_DIR" && npm install)
fi

echo "Starting backend on $BACKEND_URL"
(
  cd "$ROOT_DIR"
  PYTHONPATH="$BACKEND_DIR" exec python3 -m uvicorn app.main:app \
    --host "$BACKEND_HOST" \
    --port "$BACKEND_PORT"
) &
BACKEND_PID=$!

echo "Starting frontend on $FRONTEND_URL"
(
  cd "$FRONTEND_DIR"
  VITE_API_BASE_URL="http://$BACKEND_HOST:$BACKEND_PORT" \
    exec npm run dev -- --host "$FRONTEND_HOST" --port "$FRONTEND_PORT"
) &
FRONTEND_PID=$!

echo
echo "Stock Analysis Agent is starting:"
echo "  Frontend: $FRONTEND_URL"
echo "  Backend:  $BACKEND_URL"
echo "  API via frontend proxy: $FRONTEND_URL/api/health"
if [ "$AUTO_OPEN_BROWSER" = "1" ]; then
  echo "  Browser:  auto-open enabled"
  open_frontend "$FRONTEND_URL"
else
  echo "  Browser:  auto-open disabled"
fi
echo
echo "Press Ctrl+C to stop both servers."

exit_code=0
while true; do
  if ! kill -0 "$BACKEND_PID" 2>/dev/null; then
    wait "$BACKEND_PID" || exit_code=$?
    break
  fi
  if ! kill -0 "$FRONTEND_PID" 2>/dev/null; then
    wait "$FRONTEND_PID" || exit_code=$?
    break
  fi
  sleep 1
done

exit "$exit_code"
