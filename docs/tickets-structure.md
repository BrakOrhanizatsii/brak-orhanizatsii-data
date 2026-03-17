# Структура файлів тікетів

Кожен файл у `tickets/` — це одна тема (Epic) з усіма дочірніми тікетами.

## Файли

```
tickets/
├── shabunin-rights.tsv     ← Epic + його Stories в одному файлі
├── nabu-sap-pressure.tsv
├── midas-case.tsv
├── actors.tsv              ← список дійових осіб з email-адресами
└── _template.tsv           ← шаблон для нового файлу
```

## Структура всередині файлу

Ієрархія будується через `External Issue ID` і `Parent`:

```tsv
Work type  Summary                    External Issue ID  Parent
Epic       Справа Шабуніна...         SHABUNIN-001
Story      ДБР не відкрило...         SHABUNIN-002       SHABUNIN-001
Story      ЄСПЛ прийняв скарги...     SHABUNIN-003       SHABUNIN-001
```

- **Epic** — перший рядок у файлі, `Parent` порожній
- **Story / Task / Bug** — наступні рядки, `Parent` = ID свого Epic
- **Один файл = одна тема** — не змішувати різні Epic в один файл

## Правила іменування файлів

```
назва-теми-латиницею.tsv
```

Наприклад: `defense-procurement.tsv`, `vaks-reform.tsv`

## Правила External Issue ID

Slug у форматі `АБРЕВІАТУРА-НОМ`:

```
SHABUNIN-001
NABU-SAP-002
MIDAS-001
```

- Абревіатура — перші літери теми латиницею, 4–8 символів
- Номер — тризначний, починаючи з 001
- Унікальний глобально по всьому репо (не лише в межах файлу)

## Як це імпортується в Jira

`merge.py` зливає всі `.tsv` файли в один `import.csv`:
- Slug ID конвертуються у числові `Work item ID`
- `External Issue ID` зберігається — Jira використовує його для дедублікації при повторному імпорті
- `Parent` перераховується зі slug у числовий ID

```bash
python scripts/merge.py --output import.csv
```
