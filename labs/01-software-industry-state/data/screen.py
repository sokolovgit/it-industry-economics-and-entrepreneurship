"""Скринінг: видалення дублікатів і відбір за назвою.

Дублікати – той самий DOI або та сама нормалізована назва (препринт arXiv і його
опублікована версія). Скринінг назв – автоматичний за критеріями включення, а
його результат переглядається вручну: файл candidates.csv іде на повнотекстову оцінку.
"""

import csv
import json
import re
from pathlib import Path

HERE = Path(__file__).parent

# КВ1: мова про інструменти генерації коду / AI-асистентів
TOOL = re.compile(
    r"copilot|codex|chatgpt|gpt-?[34]|llm|large language model|generative ai|genai|"
    r"ai[- ](?:coding|pair|code|programming|assist|tool|agent)|code (?:generation|completion)|"
    r"cursor|claude|codewhisperer|ai-assisted|ai assistance|\bai\b",
    re.I,
)
# КВ2: вимірюваний результат – продуктивність, час, якість, безпека, вартість
OUTCOME = re.compile(
    r"productiv|speed|faster|time|efficien|throughput|impact|effect|quality|defect|bug|"
    r"secur|vulnerab|cost|econom|perform|evidence|measur",
    re.I,
)
# КВ3: розробка ПЗ людьми, а не загальні теми
DOMAIN = re.compile(
    r"develop|programm|software|engineer|coding|code|github|open[- ]source", re.I
)
# КВи: огляди, освіта, бенчмарки моделей без людей-розробників, вузькі домени
EXCLUDE = re.compile(
    r"systematic (?:literature )?review|literature review|survey of|mapping study|"
    r"\beducation|students?\b|classroom|course|teaching|curricul|novice|"
    r"benchmark|leaderboard|dataset|humaneval|hardware|verilog|rtl\b|"
    r"medical|clinical|health|chemistry|legal|tutorial|position paper|vision|roadmap",
    re.I,
)


def norm(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", title.lower()).strip()


def main():
    rows = list(csv.DictReader(open(HERE / "records.csv", encoding="utf-8")))
    seen, unique = set(), []
    for r in rows:
        keys = {norm(r["title"])}
        if r["doi"]:
            keys.add(r["doi"].lower())
        if keys & seen or not r["title"]:
            continue
        seen |= keys
        unique.append(r)

    passed, reasons = (
        [],
        {"no_tool": 0, "no_outcome": 0, "no_domain": 0, "excluded_topic": 0},
    )
    for r in unique:
        t = r["title"]
        if not TOOL.search(t):
            reasons["no_tool"] += 1
        elif not DOMAIN.search(t):
            reasons["no_domain"] += 1
        elif not OUTCOME.search(t):
            reasons["no_outcome"] += 1
        elif EXCLUDE.search(t):
            reasons["excluded_topic"] += 1
        else:
            passed.append(r)

    with open(HERE / "candidates.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(passed[0].keys()))
        w.writeheader()
        w.writerows(sorted(passed, key=lambda r: -int(r["cited"] or 0)))
    stats = {
        "identified": len(rows),
        "unique": len(unique),
        "duplicates": len(rows) - len(unique),
        "title_screen_passed": len(passed),
        "title_screen_excluded": reasons,
    }
    (HERE / "screen_log.json").write_text(
        json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(stats, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
