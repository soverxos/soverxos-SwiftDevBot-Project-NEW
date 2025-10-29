import sys, os, re, json
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

ROOT = Path(__file__).resolve().parent
ROADMAP_PATH = ROOT / "ROADMAP.md"
PROGRESS_PATH = ROOT / "Data" / "roadmap_progress.json"

def show_usage():
    print("Usage:")
    print("  python3 sdb.py up               # Запуск (dev info)")
    print("  python3 sdb.py down             # Остановка (skeleton info)")
    print("  python3 sdb.py module create X  # Создать модуль X")
    print("  python3 sdb.py module list      # Показать загруженные модули")
    print("  python3 sdb.py module reload X  # Перезагрузить модуль X")
    print("  python3 sdb.py progress         # Показать прогресс Roadmap")
    print("  python3 sdb.py logs [service]   # Показать логи (опционально конкретного сервиса)")
    print("  python3 sdb.py clean [mode]     # Очистить проект (cache|logs|data|all)")
    print("  python3 sdb.py status           # Статус всех сервисов")
    print("  python3 sdb.py user add <id>    # Добавить пользователя")
    print()

def create_module(name: str):
    path = os.path.join("Modules", name)
    os.makedirs(path, exist_ok=True)
    with open(os.path.join(path, "module.py"), "w", encoding="utf-8") as f:
        f.write(
            "from Systems.sdk.base_module import BaseModule\n\n"
            "class Module(BaseModule):\n"
            "    async def on_load(self):\n"
            "        print('✅ Модуль загружен: %s' % self.__class__.__name__)\n"
        )
    print(f"✅ Module created at {path}")

def analyze_roadmap():
    if not ROADMAP_PATH.exists():
        print("❌ Файл ROADMAP.md не найден.")
        return None

    text = ROADMAP_PATH.read_text(encoding="utf-8")
    total = len(re.findall(r"- \[.\]", text))
    done = len(re.findall(r"- \[x\]", text))
    percent = round((done / total * 100), 1) if total > 0 else 0

    stages = re.findall(r"## (.+?)\n([\s\S]+?)(?=## |$)", text)
    stage_progress = {}
    for title, content in stages:
        t = len(re.findall(r"- \[.\]", content))
        d = len(re.findall(r"- \[x\]", content))
        stage_progress[title.strip()] = round((d / t * 100), 1) if t > 0 else 0

    data = {"total": percent, "stages": stage_progress}
    PROGRESS_PATH.parent.mkdir(parents=True, exist_ok=True)
    PROGRESS_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    return data

def show_progress():
    data = analyze_roadmap()
    if not data:
        return
    print("\n📊 SwiftDevBot Development Progress")
    print("───────────────────────────────────────")
    print(f"🧩 Всего завершено: {data['total']}%")
    for stage, val in data["stages"].items():
        # красивый progress bar
        bar_len = 20
        filled = int(bar_len * val / 100)
        bar = "🟩" * filled + "⬛" * (bar_len - filled)
        print(f"  • {stage.ljust(35)} {bar} {val}%")
    print(f"\n💾 Прогресс сохранён → {PROGRESS_PATH}\n")

def show_logs(service=None):
    logs_dir = ROOT / "Data" / "logs"
    if not logs_dir.exists():
        print("❌ Директория логов не найдена.")
        return
    
    if service:
        log_file = logs_dir / f"{service}.log"
        if not log_file.exists():
            print(f"❌ Лог {service}.log не найден.")
            return
        print(f"\n📋 Последние 30 строк из {service}.log:\n")
        print("─" * 80)
        lines = log_file.read_text(encoding="utf-8").splitlines()
        for line in lines[-30:]:
            print(line)
        print("─" * 80)
    else:
        print("\n📋 Последние 5 строк из всех логов:\n")
        for log_file in sorted(logs_dir.glob("*.log")):
            lines = log_file.read_text(encoding="utf-8").splitlines()
            if lines:
                print(f"▶️ {log_file.name}")
                for line in lines[-5:]:
                    print(f"  {line}")
                print()

def clean_project(mode="cache"):
    """Вызов скрипта очистки проекта"""
    import subprocess
    clean_script = ROOT / "clean.sh"

    if not clean_script.exists():
        print("❌ Скрипт clean.sh не найден.")
        return

    try:
        result = subprocess.run(["bash", str(clean_script), mode], check=True)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка при выполнении clean.sh: {e}")
        return False


def list_modules():
    """Показать список загруженных модулей"""
    try:
        import requests
        response = requests.get("http://localhost:8104/modules", timeout=5)
        if response.status_code == 200:
            data = response.json()
            modules = data.get("modules", {})

            print("🧩 Loaded Modules:")
            print("=" * 50)

            if not modules:
                print("❌ No modules loaded")
                return

            for name, info in modules.items():
                status = "✅" if info.get("loaded") else "❌"
                print(f"{status} {name}")
                print(f"   📦 {info.get('name', 'Unknown')} v{info.get('version', '?.?.?')}")
                print(f"   📝 {info.get('description', 'No description')}")
                print(f"   🎯 Commands: {len(info.get('commands', []))}")
                print(f"   📡 Events: {len(info.get('events', []))}")
                print(f"   🌐 Web tabs: {len(info.get('web_tabs', []))}")
                print()
        else:
            print("❌ Failed to get modules list from module_host")
    except Exception as e:
        print(f"❌ Error connecting to module_host: {e}")
        print("   Make sure module_host service is running on port 8104")


def reload_module(module_name: str):
    """Перезагрузить модуль"""
    try:
        import requests
        response = requests.post(f"http://localhost:8104/modules/{module_name}/reload", timeout=10)
        if response.status_code == 200:
            print(f"✅ Module {module_name} reloaded successfully")
        else:
            print(f"❌ Failed to reload module {module_name}")
            print(f"   Status: {response.status_code}")
    except Exception as e:
        print(f"❌ Error reloading module: {e}")


def show_status():
    """Показать статус всех сервисов"""
    services = [
        ("bot_service", 8101),
        ("auth_service", 8102),
        ("user_service", 8103),
        ("module_host", 8104),
        ("rbac_service", 8105),
        ("admin_service", 8106),
        ("webpanel", 8000)
    ]

    print("🔍 Service Status:")
    print("=" * 40)

    for service_name, port in services:
        try:
            import requests
            response = requests.get(f"http://localhost:{port}/health", timeout=2)
            if response.status_code == 200:
                status = "✅ RUNNING"
                try:
                    data = response.json()
                    extra = f" ({data.get('modules_loaded', 'N/A')} modules)" if service_name == "module_host" else ""
                    status += extra
                except:
                    pass
            else:
                status = f"⚠️  ERROR ({response.status_code})"
        except:
            status = "❌ DOWN"

        print(f"{service_name:<15} {status}")


def add_user(user_id: str):
    """Добавить пользователя в систему"""
    try:
        user_id_int = int(user_id)
        print(f"👤 Adding user {user_id_int}...")

        # Здесь должна быть логика добавления пользователя
        # Пока просто заглушка
        print("⚠️  User management not implemented yet")
        print("   This feature will be available in Stage 3")

    except ValueError:
        print(f"❌ Invalid user ID: {user_id}")
    except Exception as e:
        print(f"❌ Error adding user: {e}")

def main():
    if len(sys.argv) < 2:
        show_usage()
        return

    cmd = sys.argv[1]

    if cmd == "up":
        print("🚀 SwiftDevBot skeleton up (dev). Use run_dev.sh to start services.")
    elif cmd == "down":
        print("🛑 SwiftDevBot down (no-op for skeleton).")
    elif cmd == "module":
        sub = sys.argv[2] if len(sys.argv) > 2 else None
        if sub == "create":
            name = sys.argv[3] if len(sys.argv) > 3 else "new_module"
            create_module(name)
        elif sub == "list":
            list_modules()
        elif sub == "reload":
            if len(sys.argv) > 3:
                reload_module(sys.argv[3])
            else:
                print("Usage: python sdb.py module reload <module_name>")
        else:
            print("Usage: python sdb.py module <create|list|reload> [args]")
    elif cmd == "progress":
        show_progress()
    elif cmd == "logs":
        service = sys.argv[2] if len(sys.argv) > 2 else None
        show_logs(service)
    elif cmd == "clean":
        mode = sys.argv[2] if len(sys.argv) > 2 else "cache"
        clean_project(mode)
    elif cmd == "status":
        show_status()
    elif cmd == "user":
        sub = sys.argv[2] if len(sys.argv) > 2 else None
        if sub == "add":
            user_id = sys.argv[3] if len(sys.argv) > 3 else None
            if user_id:
                add_user(user_id)
            else:
                print("Usage: python sdb.py user add <user_id>")
        else:
            print("Usage: python sdb.py user add <user_id>")
    else:
        print(f"❌ Unknown command: {cmd}\n")
        show_usage()

if __name__ == "__main__":
    main()
