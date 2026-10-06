"""Оцінка придатності за повним текстом і підсумкові цифри для схеми PRISMA.

На цей етап ідуть записи, що пройшли скринінг анотацій, і записи, повернуті вручну:
фільтр за ключовими словами відсіяв їх через формулювання анотації, хоча за змістом
вони відповідають критеріям. Включені дослідження перелічено явно, для решти
фіксується причина виключення.
"""

import csv
import json
import re
from pathlib import Path

HERE = Path(__file__).parent

# Відсіяні фільтром анотацій, повернуті після ручної перевірки
REINSTATED = [
    "Do Users Write More Insecure Code with AI Assistants",
    "Productivity assessment of neural code completion",
    "Impact of AI Tool on Engineering at ANZ Bank",
    "Impact of Generative AI on Collaborative Open-Source Software Development",
    "Impact of the Availability of ChatGPT on Software Development",
    "Security Weaknesses of Copilot-Generated Code in GitHub Projects",
]

# Включені за результатами оцінки повного тексту (код дослідження – фрагмент назви)
INCLUDED = {
    "Pearce2022": "Asleep at the Keyboard",
    "Ziegler2022": "Productivity assessment of neural code completion",
    "Peng2023": "The Impact of AI on Developer Productivity: Evidence from GitHub Copilot",
    "Perry2023": "Do Users Write More Insecure Code with AI Assistants",
    "Fu2023": "Security Weaknesses of Copilot-Generated Code in GitHub Projects",
    "Chatterjee2024": "Impact of AI Tool on Engineering at ANZ Bank",
    "Song2024": "Impact of Generative AI on Collaborative Open-Source Software Development",
    "Quispe2024": "Impact of the Availability of ChatGPT on Software Development",
    "Cui2025": "Three Field Experiments with Software Developers",
    "Paradis2025": "Enterprise-Based Randomized Controlled Trial",
    "Becker2025": "Early-2025 AI on Experienced Open-Source Developer Productivity",
    "Stray2026": "Developer Productivity With and Without GitHub Copilot",
    "Heilman2026": "Observational Dose-Response Analysis",
    "Borg2026": "Echoes of AI",
}

RULES = [
    (
        "Вторинне дослідження: огляд, метааналіз, синтез",
        r"meta-analysis|literature review|systematic|synthesis of|evidence synthesis|techniques, impact|future directions|evidence, measurement",
    ),
    ("Освітній контекст, студенти", r"teach|practicum|students?|education"),
    (
        "Пропозиція методу чи інструмента",
        r"framework|repair|fine-tun|dpo|plugin|graph neural|inspectcoder|vibeguard|patch learning|"
        r"guard|adversarial|attacks?|poisoning|representation selection|detection",
    ),
    (
        "Оцінка моделі без розробників і реального проєкту",
        r"llm-generated|ai-generated code|generated code|chatgpt-4o|code synthesis|"
        r"prompt|large language models and|across (?:large|programming)|runtime performance|software metrics|code smell|"
        r"generative ai coding assistants on",
    ),
]
OTHER = "Немає групи порівняння або базової лінії, лише сприйняття, чи недостатньо методологічних даних"


def main():
    full = list(csv.DictReader(open(HERE / "fulltext.csv", encoding="utf-8")))
    cand = list(csv.DictReader(open(HERE / "candidates.csv", encoding="utf-8")))
    ids = {r["id"] for r in full}
    back = [
        r
        for r in cand
        if r["id"] not in ids
        and any(k.lower() in r["title"].lower() for k in REINSTATED)
    ]
    pool = full + back

    out, included, reasons = [], {}, {}
    for r in pool:
        code = next(
            (c for c, k in INCLUDED.items() if k.lower() in r["title"].lower()), None
        )
        if code and code not in included:
            included[code] = r["title"]
            decision = f"включено ({code})"
        else:
            decision = next(
                (name for name, rx in RULES if re.search(rx, r["title"], re.I)), OTHER
            )
            reasons[decision] = reasons.get(decision, 0) + 1
        out.append(
            {
                "title": r["title"],
                "year": r["year"],
                "db": r["db"],
                "decision": decision,
            }
        )
    missing = set(INCLUDED) - set(included)
    assert not missing, f"не знайдено у вибірці: {missing}"

    with open(HERE / "eligibility.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["title", "year", "db", "decision"])
        w.writeheader()
        w.writerows(out)
    log = json.loads((HERE / "screen_log.json").read_text())
    log.update(
        {
            "reinstated_manually": len(back),
            "fulltext_assessed": len(pool),
            "fulltext_excluded": reasons,
            "included_from_search": len(included),
        }
    )
    (HERE / "screen_log.json").write_text(
        json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(
        json.dumps(
            {
                k: log[k]
                for k in [
                    "reinstated_manually",
                    "fulltext_assessed",
                    "fulltext_excluded",
                    "included_from_search",
                ]
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
