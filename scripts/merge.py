#!/usr/bin/env python3
"""
Злиття всіх TSV файлів у єдиний CSV для імпорту в Jira.
Використання: python scripts/merge.py --output import.csv
"""

import argparse
import csv
import sys
from pathlib import Path

COLUMNS = ["Work type", "Summary", "Work item ID", "Parent", "Description", "Priority", "Labels", "Assignee"]


def merge(output_path: Path):
    tickets_dir = Path(__file__).parent.parent / "tickets"
    files = sorted([f for f in tickets_dir.glob("*.tsv") if f.name != "_template.tsv"])

    if not files:
        print("⚠️  Не знайдено жодного TSV файлу в tickets/")
        sys.exit(1)

    rows = []
    global_id = 1
    id_map = {}  # (filename, local_id) -> global_id

    for filepath in files:
        print(f"  📄 {filepath.name}")
        with open(filepath, encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter="\t")
            for row in reader:
                local_id = row.get("Work item ID", "").strip()
                local_parent = row.get("Parent", "").strip()

                # Призначаємо глобальний ID
                if local_id:
                    id_map[(filepath.name, local_id)] = str(global_id)
                    row["Work item ID"] = str(global_id)
                    global_id += 1

                # Оновлюємо Parent на глобальний ID
                if local_parent:
                    global_parent = id_map.get((filepath.name, local_parent), local_parent)
                    row["Parent"] = global_parent

                rows.append(row)

    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    print(f"\n✅ Готово: {output_path} ({len(rows)} тікетів з {len(files)} файлів)")


def main():
    parser = argparse.ArgumentParser(description="Злиття TSV файлів у CSV для імпорту в Jira")
    parser.add_argument("--output", default="import.csv", help="Шлях до вихідного CSV файлу")
    args = parser.parse_args()

    output = Path(args.output)
    print(f"\n🔀 Злиття файлів з tickets/ → {output}\n")
    merge(output)


if __name__ == "__main__":
    main()
