"""report.src.md -> report.md: нумерація джерел [@Key] і вставка таблиць із результатів обчислень."""

import json
import re
from pathlib import Path

HERE = Path(__file__).parent
REPORT = HERE.parent / "docs" / "report"
D = "дата звернення: 04.11.2026"
LVL_SCREEN = {"s": "Простий", "m": "Середній", "d": "Складний"}

SOURCES = {
    "Shopizer": f"Shopizer: Java open source e-commerce software. URL: https://github.com/shopizer-ecommerce/shopizer, коміт 6a4a0a6 від 23.03.2025 ({D}).",
    "Jones1991": "Jones C. Applied Software Measurement: Assuring Productivity and Quality. New York : McGraw-Hill, 1991. 493 p.",
    "FeP": f"Extended Function Point (EFP) Metrics. GeeksforGeeks. URL: https://www.geeksforgeeks.org/software-engineering/extended-function-point-efp-metrics/ ({D}).",
    "Boehm2000": "Boehm B. W., Abts C., Brown A. W. et al. Software Cost Estimation with COCOMO II. Upper Saddle River, NJ : Prentice Hall, 2000. 544 p.",
    "Anda2005": f"Anda B., Benestad H. C., Hove S. E. A Multiple-Case Study of Software Effort Estimation based on Use Case Points. 2005 International Symposium on Empirical Software Engineering (ISESE). IEEE, 2005. URL: https://people.eecs.ku.edu/~hossein/811/Papers/Use-Case-Points/use-case-points-anda.pdf ({D}).",
    "DOU2026": f"Зарплати українських розробників – літо 2026. DOU. 13.07.2026. URL: https://dou.ua/lenta/articles/salary-report-devs-summer-2026/ ({D}).",
    "NBU": f"Офіційний курс гривні щодо іноземних валют на 04.11.2026: долар США 45.666 UAH. Національний банк України. URL: https://bank.gov.ua/NBUStatService/v1/statdirectory/exchange?valcode=USD&date=20261104&json ({D}).",
    "Jones2017": f"Jones C. Software Economics and Function Point Metrics: Thirty years of IFPUG Progress, версія 10.0. Namcook Analytics, 14.04.2017. URL: https://www.ifpug.org/wp-content/uploads/2017/04/IYSM.-Thirty-years-of-IFPUG.-Software-Economics-and-Function-Point-Metrics-Capers-Jones.pdf ({D}).",
}


def n(x, d=0):
    return f"{x:,.{d}f}".replace(",", " ")


def table(header, widths, rows):
    lines = ["| " + " | ".join(header) + " |", "| " + " | ".join("-" * w for w in widths) + " |"]
    lines += ["| " + " | ".join(r) + " |" for r in rows]
    return "\n".join(lines)


def wrap_id(s):
    return re.sub(r"(?<=[a-z])(?=[A-Z])", "\u200b", s)


def esc(s):
    return s.replace("$", "\\$")


def tables():
    import points

    p = json.loads((HERE / "points.json").read_text(encoding="utf-8"))
    out = {}
    out["TABLE_ALG"] = table(["№", "Алгоритм", "Клас або метод"], [5, 36, 59], [[str(i), a, wrap_id(c)] for i, (a, c) in enumerate(points.ALGORITHMS, 1)])
    out["TABLE_GL3"] = table(["Компоненти", "Кількість", "Бали"], [70, 14, 14], [[g, str(c), str(c * 10)] for g, c in points.GL3] + [["Разом", str(p["op"]["gl3"]), str(p["op"]["gl3_pts"])]])
    out["TABLE_SCREENS"] = table(["№", "Контролер", "Представлення", "Таблиці", "Складність", "Бали"], [6, 30, 20, 12, 16, 8],
                                  [[str(i), s["controller"], str(s["views"]), str(s["tables"]), LVL_SCREEN[s["level"]], str(s["weight"])] for i, s in enumerate(p["op"]["screens"], 1)])
    out["TABLE_ACTORS"] = table(["Актор", "Тип", "Вага"], [60, 30, 8], [[a, {1: "Простий", 2: "Середній", 3: "Складний"}[w], str(w)] for a, w, _ in points.ACTORS] + [["Разом (UAW)", "", str(p["ucp"]["uaw"])]])
    out["TABLE_UC"] = table(["№", "Варіант використання", "Транзакцій", "Складність", "Вага"], [5, 50, 14, 16, 8],
                             [[str(i), u["name"], str(u["transactions"]), LVL_SCREEN[u["level"]], str(u["weight"])] for i, u in enumerate(p["ucp"]["use_cases"], 1)] + [["", "Разом (UUCW)", "", "", str(p["ucp"]["uucw"])]])
    out["TABLE_TECH"] = table(["Фактор", "Вага", "Оцінка", "Добуток", "Обґрунтування"], [28, 9, 11, 12, 46],
                               [[t, str(w), str(v), n(w * v, 1), j] for t, w, v, j in points.TECH] + [["Разом (TFactor)", "", "", n(p["ucp"]["tfactor"], 1), ""]])
    out["TABLE_ENV"] = table(["Фактор", "Вага", "Оцінка", "Добуток", "Обґрунтування"], [28, 9, 11, 12, 46],
                              [[t, str(w), str(v), n(w * v, 1), j] for t, w, v, j in points.ENV] + [["Разом (EFactor)", "", "", n(p["ucp"]["efactor"], 1), ""]])
    e = p["economy"]
    rows = [
        ("COCOMO за LOC (ПР2)", "72.0 KLOC", e["cocomo_loc"]), ("Функціональні точки (ПР3)", f"AFP = {n(1525)}", e["fp3"]),
        ("Feature points", f"AFeP = {n(p['fep']['afep'])}", e["fep"]), ("Use-case points, метод 2", f"AFP = {n(p['ucp2']['afp'])}", e["ucp2"]),
        ("Use-case points, метод 1, 20 год", f"UCP = {n(p['ucp']['ucp'])}", e["ucp20"]), ("Use-case points, метод 1, 36 год", f"UCP = {n(p['ucp']['ucp'])}", e["ucp36"]),
        ("Object points, номінальна продуктивність", f"OP = {p['op']['op']}", e["op"]),
    ]
    out["TABLE_ECON"] = table(["Метод", "Розмір", "Трудомісткість, людино-місяців", "Вартість, \\$", "Вартість, млн грн"], [34, 20, 22, 16, 16],
                               [[a, b, n(c["effort_pm"], 1), n(c["cost_usd"]), n(c["cost_uah"] / 1e6, 1)] for a, b, c in rows])
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
