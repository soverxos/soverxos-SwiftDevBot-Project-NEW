#!/usr/bin/env python3
"""
SwiftDevBot Roadmap Progress Tracker
------------------------------------
Скрипт читает ROADMAP.md и выводит процент выполненных задач.
"""

import re
from pathlib import Path
import json

def parse_checkboxes(text: str):
    total = len(re.findall(r"- \[.?\]", text))
    done = len(re.findall(r"- \[x\]", text, flags=re.IGNORECASE))
    return total, done

def calculate_progress(file_path="ROADMAP.md"):
    path = Path(file_path)
    if not path.exists():
        print("❌ ROADMAP.md не найден!")
        return

    content = path.read_text(encoding="utf-8")
    total, done = parse_checkboxes(content)
    percent = (done / total * 100) if total else 0

    stages = re.findall(r"## .*?\n(.*?)(?=## |$)", content, flags=re.S)
    stage_data = []
    for i, block in enumerate(stages, start=1):
        t, d = parse_checkboxes(block)
        pct = (d / t * 100) if t else 0
        stage_data.append({"stage": i, "total": t, "done": d, "progress": pct})

    print("\n📊 SwiftDevBot Roadmap Progress\n" + "="*40)
    print(f"Общий прогресс: {done}/{total} задач ({percent:.1f}%)\n")

    for s in stage_data:
        print(f"Stage {s['stage']}: {s['progress']:.1f}% ({s['done']}/{s['total']})")

    # JSON summary for CI/CD or CLI integration
    summary = {
        "total_tasks": total,
        "completed": done,
        "percent": percent,
        "stages": stage_data
    }
    Path("Data/roadmap_progress.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print("\n✅ Отчёт сохранён в Data/roadmap_progress.json")

if __name__ == "__main__":
    calculate_progress()
