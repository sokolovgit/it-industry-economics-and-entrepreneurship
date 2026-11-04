"""report.src.md -> report.md: нумерація джерел [@Key] і вставка таблиць із результатів обчислень."""

import json
import re
from pathlib import Path

HERE = Path(__file__).parent
REPORT = HERE.parent / "docs" / "report"
D = "дата звернення: 04.11.2026"
PR = {"Must": "Must", "Should": "Should", "Could": "Could"}

SOURCES = {
    "Manifesto": f"Beck K., Beedle M., van Bennekum A. et al. Manifesto for Agile Software Development. 2001. URL: https://agilemanifesto.org/ ({D}).",
    "Scrum2020": f"Schwaber K., Sutherland J. The Scrum Guide. 2020. URL: https://scrumguides.org/scrum-guide.html ({D}).",
    "Cohn2005": "Cohn M. Agile Estimating and Planning. Upper Saddle River, NJ : Prentice Hall, 2005. 330 p.",
    "Shopizer": f"Shopizer: Java open source e-commerce software. URL: https://github.com/shopizer-ecommerce/shopizer, коміт 6a4a0a6 від 23.03.2025 ({D}).",
    "Jones2017": f"Jones C. Software Economics and Function Point Metrics: Thirty years of IFPUG Progress, версія 10.0. Namcook Analytics, 14.04.2017. URL: https://www.ifpug.org/wp-content/uploads/2017/04/IYSM.-Thirty-years-of-IFPUG.-Software-Economics-and-Function-Point-Metrics-Capers-Jones.pdf ({D}).",
    "DOU2026": f"Зарплати українських розробників – літо 2026. DOU. 13.07.2026. URL: https://dou.ua/lenta/articles/salary-report-devs-summer-2026/ ({D}).",
    "NBU": f"Офіційний курс гривні щодо іноземних валют на 04.11.2026: долар США 45.666 UAH. Національний банк України. URL: https://bank.gov.ua/NBUStatService/v1/statdirectory/exchange?valcode=USD&date=20261104&json ({D}).",
}


def n(x, d=0):
    return f"{x:,.{d}f}".replace(",", " ")


def table(header, widths, rows):
    lines = ["| " + " | ".join(header) + " |", "| " + " | ".join("-" * w for w in widths) + " |"]
    lines += ["| " + " | ".join(r) + " |" for r in rows]
    return "\n".join(lines)


def tables():
    S = json.loads((HERE / "scrum.json").read_text(encoding="utf-8"))
    out = {}
    out["TABLE_BACKLOG"] = table(["ID", "Пріоритет", "Користувацька історія", "Операцій", "UFP"], [10, 14, 48, 14, 10],
                                  [[s["id"], s["priority"], s["text"], str(s["ops"]), str(s["ufp"])] for s in S["stories"]] + [["", "", "Разом", str(sum(s["ops"] for s in S["stories"])), str(sum(s["ufp"] for s in S["stories"]))]])
    ta, tb = S["teams"]["A"]["stories"], S["teams"]["B"]["stories"]
    rows = [[s["id"], s["title"], n(s["ref_days"], 1), str(a["sp"]), str(a["rounds"]), str(b["sp"]), str(b["rounds"])] for s, a, b in zip(S["stories"], ta, tb)]
    rows.append(["", "Разом", n(sum(s["ref_days"] for s in S["stories"]), 1), str(sum(a["sp"] for a in ta)), "", str(sum(b["sp"] for b in tb)), ""])
    out["TABLE_VOTES"] = table(["ID", "Історія", "Довідково, дні", "A, SP", "A, раундів", "B, SP", "B, раундів"], [9, 28, 16, 10, 13, 10, 14], rows)
    m = S["methods"]
    rows = []
    for k in ("Planning Poker, команда A", "Planning Poker, команда B", "T-shirt, команда A", "T-shirt, команда B"):
        v = m[k]
        rows.append([k, n(v["total"]), n(v["rounds"], 2), n(v["mre"] * 100, 1), n(v["spearman_ufp"], 2)])
    out["TABLE_METHODS"] = table(["Метод і команда", "Разом SP", "Раундів на історію", "Похибка, %", "Кореляція з UFP"], [32, 12, 18, 14, 18], rows)
    plan = {}
    for p in S["plan"]:
        plan.setdefault(p["sprint"], []).append(p)
    rows = [[str(k), ", ".join(f"{p['id']} ({p['sp']})" for p in v), str(sum(p["sp"] for p in v))] for k, v in sorted(plan.items())]
    out["TABLE_PLAN"] = table(["Спринт", "Історії (SP)", "Разом SP"], [11, 78, 11], rows)
    e = S["eco"]
    rows = [
        ["Команда A", n(e["A"]["sp"]), n(e["A"]["sprints"]), n(e["A"]["weeks"]), n(e["A"]["pm"], 1), n(e["A"]["cost_usd"]), n(e["A"]["cost_uah"] / 1e6, 2), n(e["A"]["usd_per_sp"])],
        ["Команда B", n(e["B"]["sp"]), n(e["B"]["sprints"]), n(e["B"]["weeks"]), n(e["B"]["pm"], 1), n(e["B"]["cost_usd"]), n(e["B"]["cost_uah"] / 1e6, 2), n(e["B"]["usd_per_sp"])],
        ["За функціональними точками", f"AFP = {n(e['fp']['afp'])}", "–", "–", n(e["fp"]["pm"], 1), n(e["fp"]["cost_usd"]), n(e["fp"]["cost_usd"] * 45.666 / 1e6, 2), n(e["fp"]["usd_per_afp"]) + " за FP"],
    ]
    out["TABLE_ECON"] = table(["Оцінка", "Обсяг", "Спр.", "Тижні", "PM", "Вартість, \\$", "Млн грн", "\\$ за од."], [22, 11, 9, 10, 9, 14, 11, 14], rows)
    return out


def main():
    src = (REPORT / "report.src.md").read_text(encoding="utf-8")
    for k, v in tables().items():
        src = src.replace(f"<!-- {k} -->", v)
    order: list[str] = []

    def num(key):
        if key not in SOURCES:
            raise SystemExit(f"невідоме джерело: {key}")
        if key not in order:
            order.append(key)
        return str(order.index(key) + 1)

    body = re.sub(r"\[@([\w,;\s@]+)\]", lambda m: "[" + ", ".join(num(k.strip().lstrip("@")) for k in re.split(r"[,;]", m.group(1))) + "]", src)
    refs = "\n".join(f"{i}. {SOURCES[k]}" for i, k in enumerate(order, start=1))
    body = body.replace("<!-- SOURCES -->", refs)
    (REPORT / "report.md").write_text(body, encoding="utf-8")
    print(f"посилань: {len(order)}; не використано: {sorted(set(SOURCES) - set(order))}")


if __name__ == "__main__":
    main()
