#!/usr/bin/env bash
# ===========================================
# SwiftDevBot - Cleanup Script
# ===========================================
# Очистка проекта от кеша, логов и временных файлов

set -e

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  🧹 SwiftDevBot Cleanup Utility${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

show_usage() {
    echo "Usage: bash clean.sh [MODE]"
    echo ""
    echo "Modes:"
    echo "  cache      - Очистить Python кеш (__pycache__, *.pyc)"
    echo "  logs       - Очистить логи (Data/logs/*.log)"
    echo "  pids       - Очистить pid файлы (Data/pids/*.pid)"
    echo "  data       - Очистить все данные (logs + pids + uploads)"
    echo "  all        - Полная очистка (cache + data)"
    echo "  deep       - Глубокая очистка (all + venv rebuild)"
    echo ""
    echo "Examples:"
    echo "  bash clean.sh cache   # Только кеш Python"
    echo "  bash clean.sh all     # Кеш + данные"
    echo ""
}

clean_python_cache() {
    echo -e "${YELLOW}🗑️  Очистка Python кеша...${NC}"
    
    # Удаляем __pycache__
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    
    # Удаляем .pyc и .pyo файлы
    find . -type f -name "*.pyc" -delete 2>/dev/null || true
    find . -type f -name "*.pyo" -delete 2>/dev/null || true
    
    # Удаляем .pytest_cache
    find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
    
    # Удаляем .mypy_cache
    find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
    
    # Удаляем .coverage
    find . -type f -name ".coverage" -delete 2>/dev/null || true
    find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
    
    echo -e "${GREEN}✅ Python кеш очищен${NC}"
}

clean_logs() {
    echo -e "${YELLOW}🗑️  Очистка логов...${NC}"
    
    if [ -d "Data/logs" ]; then
        rm -f Data/logs/*.log 2>/dev/null || true
        echo -e "${GREEN}✅ Логи очищены${NC}"
    else
        echo -e "${BLUE}ℹ️  Директория Data/logs не найдена${NC}"
    fi
}

clean_pids() {
    echo -e "${YELLOW}🗑️  Очистка PID файлов...${NC}"
    
    if [ -d "Data/pids" ]; then
        rm -f Data/pids/*.pid 2>/dev/null || true
        echo -e "${GREEN}✅ PID файлы очищены${NC}"
    else
        echo -e "${BLUE}ℹ️  Директория Data/pids не найдена${NC}"
    fi
}

clean_uploads() {
    echo -e "${YELLOW}🗑️  Очистка загруженных файлов...${NC}"
    
    if [ -d "Data/uploads" ]; then
        # Удаляем все кроме .gitkeep
        find Data/uploads -type f ! -name ".gitkeep" -delete 2>/dev/null || true
        echo -e "${GREEN}✅ Загруженные файлы очищены${NC}"
    else
        echo -e "${BLUE}ℹ️  Директория Data/uploads не найдена${NC}"
    fi
}

clean_database() {
    echo -e "${YELLOW}🗑️  Очистка баз данных...${NC}"
    
    if [ -d "Data/database" ]; then
        # Удаляем все кроме .gitkeep
        find Data/database -type f ! -name ".gitkeep" -delete 2>/dev/null || true
        echo -e "${GREEN}✅ Базы данных очищены${NC}"
    else
        echo -e "${BLUE}ℹ️  Директория Data/database не найдена${NC}"
    fi
}

clean_backups() {
    echo -e "${YELLOW}🗑️  Очистка бэкапов...${NC}"
    
    if [ -d "Backups" ]; then
        # Удаляем все кроме .gitkeep
        find Backups -type f ! -name ".gitkeep" -delete 2>/dev/null || true
        echo -e "${GREEN}✅ Бэкапы очищены${NC}"
    else
        echo -e "${BLUE}ℹ️  Директория Backups не найдена${NC}"
    fi
}

clean_temp_files() {
    echo -e "${YELLOW}🗑️  Очистка временных файлов...${NC}"
    
    # Удаляем временные файлы
    find . -type f -name "*.tmp" -delete 2>/dev/null || true
    find . -type f -name "*.bak" -delete 2>/dev/null || true
    find . -type f -name "*.swp" -delete 2>/dev/null || true
    find . -type f -name "*.swo" -delete 2>/dev/null || true
    find . -type f -name "*~" -delete 2>/dev/null || true
    
    echo -e "${GREEN}✅ Временные файлы очищены${NC}"
}

rebuild_venv() {
    echo -e "${YELLOW}🔄 Пересборка виртуального окружения...${NC}"
    
    if [ -d ".venv" ]; then
        echo -e "${RED}⚠️  Удаление .venv${NC}"
        rm -rf .venv
    fi
    
    echo -e "${BLUE}📦 Создание нового виртуального окружения...${NC}"
    python3 -m venv .venv
    
    echo -e "${BLUE}📥 Установка зависимостей...${NC}"
    .venv/bin/pip install --upgrade pip > /dev/null 2>&1
    .venv/bin/pip install -r requirements.txt
    
    echo -e "${GREEN}✅ Виртуальное окружение пересоздано${NC}"
}

show_stats() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}📊 Статистика проекта:${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    # Размер директории
    total_size=$(du -sh . 2>/dev/null | cut -f1)
    echo -e "  Общий размер: ${GREEN}${total_size}${NC}"
    
    # Количество Python файлов
    py_count=$(find . -name "*.py" -not -path "./.venv/*" 2>/dev/null | wc -l)
    echo -e "  Python файлов: ${GREEN}${py_count}${NC}"
    
    # Количество __pycache__
    cache_count=$(find . -type d -name "__pycache__" 2>/dev/null | wc -l)
    echo -e "  Директорий __pycache__: ${GREEN}${cache_count}${NC}"
    
    # Количество .pyc файлов
    pyc_count=$(find . -type f -name "*.pyc" 2>/dev/null | wc -l)
    echo -e "  Файлов .pyc: ${GREEN}${pyc_count}${NC}"
    
    # Логи
    if [ -d "Data/logs" ]; then
        log_count=$(find Data/logs -name "*.log" 2>/dev/null | wc -l)
        echo -e "  Лог-файлов: ${GREEN}${log_count}${NC}"
    fi
    
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

# ==========================================
# Main Logic
# ==========================================

print_header

MODE="${1:-help}"

case "$MODE" in
    cache)
        clean_python_cache
        clean_temp_files
        show_stats
        ;;
    
    logs)
        clean_logs
        ;;
    
    pids)
        clean_pids
        ;;
    
    data)
        clean_logs
        clean_pids
        clean_uploads
        echo -e "${GREEN}✨ Данные очищены${NC}"
        ;;
    
    all)
        clean_python_cache
        clean_temp_files
        clean_logs
        clean_pids
        clean_uploads
        echo ""
        echo -e "${GREEN}✨ Проект полностью очищен${NC}"
        show_stats
        ;;
    
    deep)
        echo -e "${RED}⚠️  ВНИМАНИЕ: Глубокая очистка включает удаление виртуального окружения!${NC}"
        read -p "Продолжить? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            clean_python_cache
            clean_temp_files
            clean_logs
            clean_pids
            clean_uploads
            clean_database
            clean_backups
            rebuild_venv
            echo ""
            echo -e "${GREEN}✨ Глубокая очистка завершена${NC}"
            show_stats
        else
            echo -e "${YELLOW}❌ Отменено${NC}"
        fi
        ;;
    
    stats)
        show_stats
        ;;
    
    help|--help|-h|*)
        show_usage
        exit 0
        ;;
esac

echo ""
echo -e "${GREEN}🎉 Готово!${NC}"

