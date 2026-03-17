#!/usr/bin/env python3
"""
Валідація TSV файлів перед імпортом у Jira.
Використання: python scripts/validate.py --file tickets/example.tsv
              python scripts/validate.py --all
"""

import argparse
import csv
import sys
from pathlib import Path

REQUIRED_COLUMNS = {"Work type", "Summary", "Work item ID"}
VALID_WORK_TYPES = {"Epic", "Story", "Task", "Bug", "Subtask"}
VALID_PRIORITIES = {"Highest", "High", "Medium", "Low", ""}
MAX_SUMMARY_LENGTH = 200

errors = []
warnings = []


def error(file, row, msg):
    errors.append(f"  ❌ [{file}] рядок {row}: {msg}")


def warn(file, row, msg):
    warnings.append(f"  ⚠️  [{file}] рядок {row}: {msg}")


def validate_file(filepath: Path):
    filename = filepath.name
    print(f"\n🔍 Перевірка: {filepath}")

    with open(filepath, encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")

        # Перевірка обов'язкових колонок
        if not reader.fieldnames:
            error(filename, 1, "Файл порожній або немає заголовків")
            return

        missing = REQUIRED_COLUMNS - set(reader.fieldnames)
        if missing:
            error(filename, 1, f"Відсутні обов'язкові колонки: {', '.join(missing)}")
            return

        seen_ids = {}

        for i, row in enumerate(reader, start=2):
            item_id = row.get("Work item ID", "").strip()
            summary = row.get("Summary", "").strip()
            work_type = row.get("Work type", "").strip()
            priority = row.get("Priority", "").strip()
            parent = row.get("Parent", "").strip()
            description = row.get("Description", "").strip()

            # Унікальність ID
            if item_id:
                if item_id in seen_ids:
                    error(filename, i, f"Дублікат Work item ID: {item_id} (вже є в рядку {seen_ids[item_id]})")
                else:
                    seen_ids[item_id] = i

            # Summary обов'язковий
            if not summary:
                error(filename, i, "Summary порожній")
            elif len(summary) > MAX_SUMMARY_LENGTH:
                error(filename, i, f"Summary перевищує {MAX_SUMMARY_LENGTH} символів ({len(summary)})")

            # Work type
            if work_type not in VALID_WORK_TYPES:
                error(filename, i, f"Невідомий Work type: '{work_type}'. Допустимі: {', '.join(VALID_WORK_TYPES)}")

            # Priority
            if priority not in VALID_PRIORITIES:
                warn(filename, i, f"Невідомий Priority: '{priority}'. Допустимі: Highest, High, Medium, Low")

            # Parent посилається на існуючий ID
            if parent and parent not in seen_ids:
                warn(filename, i, f"Parent '{parent}' ще не зустрічався — переконайся що Epic оголошений вище")

            # Description для Story/Bug
            if work_type in {"Story", "Bug"} and not description:
                warn(filename, i, "Description порожній для Story/Bug")


def main():
    parser = argparse.ArgumentParser(description="Валідація TSV файлів тікетів")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--file", help="Шлях до конкретного TSV файлу")
    group.add_argument("--all", action="store_true", help="Перевірити всі файли в tickets/")
    args = parser.parse_args()

    files = []
    if args.all:
        tickets_dir = Path(__file__).parent.parent / "tickets"
        files = [f for f in tickets_dir.glob("*.tsv") if f.name != "_template.tsv"]
        if not files:
            print("⚠️  Не знайдено жодного TSV файлу в tickets/")
            sys.exit(0)
    else:
        path = Path(args.file)
        if not path.exists():
            print(f"❌ Файл не знайдено: {path}")
            sys.exit(1)
        files = [path]

    for f in files:
        validate_file(f)

    print()
    if warnings:
        print("Попередження:")
        for w in warnings:
            print(w)
    if errors:
        print("\nПомилки:")
        for e in errors:
            print(e)
        print(f"\n💥 Знайдено {len(errors)} помилок. Виправ їх перед імпортом.")
        sys.exit(1)
    else:
        print(f"✅ Перевірено {len(files)} файл(ів). Помилок не знайдено.")


if __name__ == "__main__":
    main()
