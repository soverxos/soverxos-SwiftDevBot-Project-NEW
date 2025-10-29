#!/usr/bin/env bash
set -e

CMD="${1:-start}"
LOG_DIR="Data/logs"
PID_DIR="Data/pids"

mkdir -p "$LOG_DIR" "$PID_DIR" "Data/database" "Data/uploads"

install_deps() {
  echo "📦 Installing Python deps..."
  if [ -d ".venv" ]; then
    .venv/bin/pip install -r requirements.txt
  else
    pip install -r requirements.txt
  fi
}

start_service() {
  local name="$1"
  local module_path="$2"
  local port="$3"
  local log="$LOG_DIR/${name}.log"
  local python_bin="python"
  [ -d ".venv" ] && python_bin=".venv/bin/python"
  echo "▶️  Starting ${name} on port ${port} ..."
  # -u flag для unbuffered output (логи пишутся сразу)
  nohup "$python_bin" -u "${module_path}" > "$log" 2>&1 &
  echo $! > "$PID_DIR/${name}.pid"
}

stop_service() {
  local name="$1"
  local pid_file="$PID_DIR/${name}.pid"
  if [ -f "$pid_file" ]; then
    PID=$(cat "$pid_file")
    echo "⏹  Stopping ${name} (pid $PID) ..."
    kill "$PID" || true
    rm -f "$pid_file"
  fi
}

status_service() {
  local name="$1"
  local pid_file="$PID_DIR/${name}.pid"
  if [ -f "$pid_file" ]; then
    PID=$(cat "$pid_file")
    if ps -p "$PID" > /dev/null; then
      echo "✅ ${name} running (pid $PID)"
    else
      echo "❌ ${name} not running (stale pid file)"
    fi
  else
    echo "❌ ${name} not running"
  fi
}

case "$CMD" in
  start)
    install_deps
    start_service "webpanel" "Systems/SysModules/webpanel/backend/main.py" "8000"
    start_service "auth_service"   "Systems/services/auth_service/main.py"   "8101"
    start_service "user_service"   "Systems/services/user_service/main.py"   "8102"
    start_service "rbac_service"   "Systems/services/rbac_service/main.py"   "8103"
    start_service "module_host"    "Systems/services/module_host/main.py"    "8104"
    start_service "admin_service"  "Systems/services/admin_service/main.py"  "8105"
    start_service "bot_service"    "Systems/services/bot_service/main.py"    "N/A"
    echo "🚀 All services started. Logs → $LOG_DIR"
    ;;
  stop)
    for s in webpanel auth_service user_service rbac_service module_host admin_service bot_service; do
      stop_service "$s"
    done
    echo "🛑 All services stopped."
    ;;
  status)
    for s in webpanel auth_service user_service rbac_service module_host admin_service bot_service; do
      status_service "$s"
    done
    ;;
  *)
    echo "Usage: bash run_dev.sh [start|stop|status]"
    exit 1
    ;;
esac
