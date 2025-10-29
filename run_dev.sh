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

  # Для FastAPI сервисов используем uvicorn
  if [[ "$name" == "bot_service" ]]; then
    # bot_service запускается напрямую
    nohup "$python_bin" -u "${module_path}" > "$log" 2>&1 &
  else
    # Остальные сервисы - FastAPI приложения
    nohup "$python_bin" -m uvicorn "${module_path}:app" --host 0.0.0.0 --port "$port" > "$log" 2>&1 &
  fi
  echo $! > "$PID_DIR/${name}.pid"
}

stop_service() {
  local name="$1"
  local pid_file="$PID_DIR/${name}.pid"

  # Сначала пытаемся остановить по PID
  if [ -f "$pid_file" ]; then
    PID=$(cat "$pid_file")
    echo "⏹  Stopping ${name} (pid $PID) ..."
    kill "$PID" 2>/dev/null || true
    rm -f "$pid_file"
  fi

  # Для FastAPI сервисов также проверяем и убиваем процессы на портах
  if [[ "$name" != "bot_service" ]]; then
    local port=""
    case "$name" in
      webpanel) port="8000" ;;
      auth_service) port="8101" ;;
      user_service) port="8102" ;;
      rbac_service) port="8103" ;;
      module_host) port="8104" ;;
      admin_service) port="8105" ;;
    esac

    if [ -n "$port" ]; then
      # Находим и убиваем процессы, слушающие на этом порту
      local pids=$(netstat -tlnp 2>/dev/null | grep ":$port " | awk '{print $7}' | cut -d'/' -f1 | sort | uniq)
      if [ -n "$pids" ]; then
        echo "⏹  Killing remaining ${name} processes on port $port ..."
        echo "$pids" | xargs kill 2>/dev/null || true
        sleep 1
        # Принудительно убиваем, если не завершились
        echo "$pids" | xargs kill -9 2>/dev/null || true
      fi
    fi
  fi
}

status_service() {
  local name="$1"
  local pid_file="$PID_DIR/${name}.pid"

  # Для FastAPI сервисов проверяем по порту, а не по PID
  if [[ "$name" == "bot_service" ]]; then
    # bot_service проверяем по PID
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
  else
    # Для FastAPI сервисов проверяем порт
    local port=""
    case "$name" in
      webpanel) port="8000" ;;
      auth_service) port="8101" ;;
      user_service) port="8102" ;;
      rbac_service) port="8103" ;;
      module_host) port="8104" ;;
      admin_service) port="8105" ;;
    esac

    if [ -n "$port" ] && netstat -tln 2>/dev/null | grep -q ":$port "; then
      echo "✅ ${name} running (port $port)"
    else
      echo "❌ ${name} not running"
    fi
  fi
}

case "$CMD" in
  start)
    install_deps
    start_service "webpanel" "Systems.SysModules.webpanel.backend.main" "8000"
    start_service "auth_service"   "Systems.services.auth_service.main"   "8101"
    start_service "user_service"   "Systems.services.user_service.main"   "8102"
    start_service "rbac_service"   "Systems.services.rbac_service.main"   "8103"
    start_service "module_host"    "Systems.services.module_host.main"    "8104"
    start_service "admin_service"  "Systems.services.admin_service.main"  "8105"
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
