#!/usr/bin/env python3
"""
Конвертує текст GitHub Issue у рядок TSV і додає до відповідного файлу епіка.

Використання:
  1. Відкрий Issue на GitHub
  2. Скопіюй весь текст Issue у файл (наприклад issue.txt)
  3. Запусти: python scripts/issue-to-tsv.py --issue 42 --file issue.txt

  Або через stdin:
  pbpaste | python scripts/issue-to-tsv.py --issue 42
"""

import argparse
import csv
import re
import sys
from pathlib import Path

TICKETS_DIR = Path(__file__).parent.parent / "tickets"

# Відповідність назви Epic → файл
# Оновлюй при додаванні нових файлів
EPIC_MAP = {
    "справа шабуніна":              "shabunin-rights.tsv",
    "права детективів набу":        "shabunin-rights.tsv",
    "тиск на набу":                 "nabu-sap-pressure.tsv",
    "набу і сап":                   "nabu-sap-pressure.tsv",
    "справа мідас":                 "midas-case.tsv",
    "галущенко":                    "midas-case.tsv",
    "відповідальність нардепів":    "officials.tsv",
    "відповідальність чиновників":  "officials.tsv",
    "оборонні закупівлі":           "defense-procurement.tsv",
    "агенція оборонних":            "defense-procurement.tsv",
    "судова реформа":               "vaks-reform.tsv",
    "вакс":                         "vaks-reform.tsv",
}


def parse_issue(text: str) -> dict:
    """Парсить текст GitHub Issue у словник полів."""

    def extract(label: str) -> str:
        """Витягує значення поля після заголовку ### Label"""
        pattern = rf"###\s*{re.escape(label)}\s*\n+(.*?)(?=\n###|\Z)"
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return ""

    # Збираємо Description з кількох полів
    context = extract("📖 Контекст")
    source = extract("🔎 Джерело")
    ac = extract("✅ Acceptance Criteria")
    blocked = extract("🚫 Причина блокування")
    notes = extract("💬 Додаткові нотатки")

    description_parts = []
    if context:
        description_parts.append(f"* Контекст: {context}")
    if source:
        description_parts.append(f"* Джерело: {source}")
    if ac:
        description_parts.append(f"* Acceptance Criteria: {ac}")
    if blocked:
        description_parts.append(f"* Причина блокування: {blocked}")
    if notes:
        description_parts.append(f"* Нотатки: {notes}")

    description = "\\n".join(description_parts)

    return {
        "summary":     extract("📌 Назва тікету (Summary)"),
        "work_type":   extract("🏷️ Тип тікету") or extract("Тип тікету"),
        "parent_epic": extract("🔗 До якого Epic належить?") or extract("До якого Epic належить"),
        "status":      extract("📊 Статус") or extract("Статус") or "To Do",
        "priority":    extract("🔥 Пріоритет") or extract("Пріоритет") or "Medium",
        "labels":      extract("🏷 Мітки (Labels)") or extract("Мітки"),
        "assignee":    extract("👤 Відповідальний (Assignee)") or extract("Відповідальний"),
        "description": description,
    }


def find_tsv_file(epic_hint: str) -> Path | None:
    """Знаходить TSV файл за назвою Epic."""
    hint_lower = epic_hint.lower()

    for keyword, filename in EPIC_MAP.items():
        if keyword in hint_lower:
            return TICKETS_DIR / filename

    return None


def next_slug(tsv_path: Path) -> str:
    """Генерує наступний slug ID для файлу."""
    stem = tsv_path.stem.upper().replace("-", "_")[:8]
    # Скорочення назви файлу до 6 символів
    parts = tsv_path.stem.split("-")
    prefix = "".join(p[:3].upper() for p in parts[:2])

    existing_ids = []
    if tsv_path.exists():
        with open(tsv_path, encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter="\t")
            for row in reader:
                slug = row.get("External Issue ID", "")
                match = re.search(r"-(\d+)$", slug)
                if match:
                    existing_ids.append(int(match.group(1)))

    next_num = max(existing_ids, default=0) + 1
    return f"{prefix}-{next_num:03d}"


def append_to_tsv(tsv_path: Path, row: dict):
    """Додає рядок до TSV файлу."""
    fieldnames = [
        "Work type", "Summary", "External Issue ID", "Parent",
        "Description", "Priority", "Labels", "Assignee", "Reporter", "Status"
    ]

    file_exists = tsv_path.exists()

    with open(tsv_path, "a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t", extrasaction="ignore")
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)


def main():
    parser = argparse.ArgumentParser(description="Конвертує текст GitHub Issue у TSV рядок")
    parser.add_argument("--issue", required=True, help="Номер Issue (для логів)")
    parser.add_argument("--file", help="Файл з текстом Issue (якщо не вказано — читає зі stdin)")
    args = parser.parse_args()

    # Читаємо текст Issue
    if args.file:
        with open(args.file, encoding="utf-8") as f:
            text = f.read()
    else:
        print("Вставте текст Issue і натисніть Ctrl+D (Mac/Linux) або Ctrl+Z (Windows):")
        text = sys.stdin.read()

    if not text.strip():
        print("❌ Порожній текст. Передай текст Issue через --file або stdin.")
        sys.exit(1)

    # Парсимо поля
    fields = parse_issue(text)

    # Перевірка обов'язкових полів
    if not fields["summary"]:
        print("❌ Не знайдено поле Summary. Перевір формат тексту Issue.")
        sys.exit(1)

    # Знаходимо файл епіка
    tsv_path = find_tsv_file(fields["parent_epic"])

    if tsv_path is None:
        print(f"\n⚠️  Не вдалося знайти TSV файл для Epic: '{fields['parent_epic']}'")
        print("\nДоступні файли:")
        for f in sorted(TICKETS_DIR.glob("*.tsv")):
            if f.name != "_template.tsv":
                print(f"  - {f.name}")
        print("\nЩо робити:")
        print("  1. Додай новий запис у EPIC_MAP у цьому скрипті")
        print("  2. Або створи новий .tsv файл вручну з tickets/_template.tsv")
        sys.exit(1)

    # Генеруємо slug
    slug = next_slug(tsv_path)

    # Формуємо рядок
    row = {
        "Work type":        fields["work_type"] or "Story",
        "Summary":          fields["summary"],
        "External Issue ID": slug,
        "Parent":           "",  # мейнтейнер вказує вручну якщо потрібно
        "Description":      fields["description"],
        "Priority":         fields["priority"],
        "Labels":           fields["labels"],
        "Assignee":         fields["assignee"],
        "Reporter":         "",
        "Status":           fields["status"],
    }

    # Показуємо превʼю
    print(f"\n📋 Issue #{args.issue} → {tsv_path.name}")
    print(f"   ID:       {slug}")
    print(f"   Type:     {row['Work type']}")
    print(f"   Summary:  {row['Summary']}")
    print(f"   Priority: {row['Priority']}")
    print(f"   Status:   {row['Status']}")
    print(f"   Assignee: {row['Assignee']}")
    print(f"   Labels:   {row['Labels']}")
    print()

    # Підтвердження
    confirm = input(f"Додати до {tsv_path.name}? [y/N] ").strip().lower()
    if confirm != "y":
        print("Скасовано.")
        sys.exit(0)

    append_to_tsv(tsv_path, row)
    print(f"\n✅ Додано {slug} до {tsv_path}")
    print(f"   Перевір файл і при потребі вкажи Parent вручну.")


if __name__ == "__main__":
    main()
