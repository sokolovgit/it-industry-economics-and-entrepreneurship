"""report.src.md -> report.md: нумерація джерел [@Key] і вставка таблиць із результатів обчислень."""

import json
import re
from pathlib import Path

HERE = Path(__file__).parent
REPORT = HERE.parent / "docs" / "report"
D = "дата звернення: 04.11.2026"
SALARY, RATE = 2500, 45.666

SOURCES = {
    "Shepperd1997": "Shepperd M., Schofield C. Estimating Software Project Effort Using Analogies. IEEE Transactions on Software Engineering. 1997. Vol. 23, No. 11. P. 736–743. DOI: 10.1109/32.637387.",
    "Conte1986": "Conte S. D., Dunsmore H. E., Shen V. Y. Software Engineering Metrics and Models. Menlo Park, CA : Benjamin/Cummings, 1986. 396 p.",
    "Cloc": f"Adler D. cloc: Count Lines of Code, версія 2.10. URL: https://github.com/AlDanial/cloc ({D}).",
    "Shopizer": f"Shopizer: Java open source e-commerce software. URL: https://github.com/shopizer-ecommerce/shopizer, коміт 6a4a0a6 від 23.03.2025 ({D}).",
    "DOU2026": f"Зарплати українських розробників – літо 2026. DOU. 13.07.2026. URL: https://dou.ua/lenta/articles/salary-report-devs-summer-2026/ ({D}).",
    "NBU": f"Офіційний курс гривні щодо іноземних валют на 04.11.2026: долар США 45.666 UAH. Національний банк України. URL: https://bank.gov.ua/NBUStatService/v1/statdirectory/exchange?valcode=USD&date=20261104&json ({D}).",
}


def n(x, d=0):
    return f"{x:,.{d}f}".replace(",", " ")


def table(header, widths, rows):
    lines = ["| " + " | ".join(header) + " |", "| " + " | ".join("-" * w for w in widths) + " |"]
    lines += ["| " + " | ".join(r) + " |" for r in rows]
    return "\n".join(lines)


def link(repo):
    return "github.com/" + repo.replace("/", "/​")


def tables():
    A = json.loads((HERE / "analogy.json").read_text(encoding="utf-8"))
    near = {d["repo"]: i for i, d in enumerate(sorted(A["distances"], key=lambda d: d["euclid"])[:3], 1)}
    near_m = {d["repo"]: i for i, d in enumerate(sorted(A["distances"], key=lambda d: d["manhattan"])[:3], 1)}
    out = {}
    rows = [[str(i), link(p["repo"]), p["commit"], "Java", n(p["kloc"], 1), str(p["effort"])] for i, p in enumerate(A["analogs"], 1)]
    new = A["new"]
    rows.append(["нов.", link(new["repo"]), new["commit"], "Java", n(new["kloc"], 1), "–"])
    out["TABLE_DB"] = table(["№", "Проєкт", "Коміт", "Мова", "Розмір, KLOC", "Зусилля"], [8, 34, 14, 8, 14, 12], rows)
    names = lambda p: p["repo"].split("/")[1]
    rows = [[str(i), names(p), str(p["modules"]), str(p["deps"]), n(p["test_share"], 1), n(p["comment_ratio"], 1), str(p["beans"]), str(p["endpoints"])] for i, p in enumerate(A["analogs"], 1)]
    rows.append(["нов.", names(new), str(new["modules"]), str(new["deps"]), n(new["test_share"], 1), n(new["comment_ratio"], 1), str(new["beans"]), str(new["endpoints"])])
    out["TABLE_ATTR"] = table(["№", "Проєкт", "Мод.", "Залеж.", "Тести, %", "Комент., %", "Компон.", "Ендп."], [8, 24, 9, 13, 11, 14, 12, 9], rows)
    d = sorted(A["distances"], key=lambda x: x["euclid"])
    rows = []
    for i, x in enumerate(d, 1):
        mark = f"№{near[x['repo']]} за Евклідом" if x["repo"] in near else ""
        if x["repo"] in near_m:
            mark = (mark + "; " if mark else "") + f"№{near_m[x['repo']]} за Манхеттеном"
        row = [str(i), x["repo"].split("/")[1], n(x["euclid"], 3), n(x["manhattan"], 3), mark]
        if mark:
            row = [f"**{c}**" if c else c for c in row]
        rows.append(row)
    out["TABLE_DIST"] = table(["№", "Проєкт", "Евклід", "Манхеттен", "Найближчі"], [8, 30, 12, 14, 34], rows)
    rows = []
    for title, key in (("Евклід, k = 3, середнє", "main"), ("Евклід, k = 3, середнє з корекцією за розміром", "main_adj"), ("Манхеттен, k = 3, середнє", "main_manhattan"), ("Манхеттен, k = 3, середнє з корекцією за розміром", "main_manhattan_adj"), ("Калібрована конфігурація: Манхеттен, k = 2, з корекцією", "best_est")):
        e = A[key]
        rows.append([title, ", ".join(x.split("/")[1] for x in e["near"]), n(e["estimate"], 1), n(e["cost_usd"]), n(e["cost_uah"] / 1e6, 1)])
    out["TABLE_EST"] = table(["Конфігурація", "Найближчі проєкти", "Зусилля", "Вартість, \\$", "Вартість, млн грн"], [28, 28, 14, 15, 15], rows)
    rows = []
    for metric, mname in (("euclid", "Евклід"), ("manhattan", "Манхеттен")):
        for adj in (False, True):
            for k in (1, 2, 3, 4, 5):
                c = next(c for c in A["configs"] if c["metric"] == metric and c["k"] == k and c["stat"] == "mean" and c["size_adj"] == adj)
                rows.append([mname, "так" if adj else "ні", str(k), n(c["mmre"] * 100), n(c["mdmre"] * 100), n(c["pred25"] * 100), n(c["pred50"] * 100)])
    out["TABLE_CALIB"] = table(["Метрика", "Корекція", "k", "MMRE, %", "MdMRE, %", "Pred(25), %", "Pred(50), %"], [14, 12, 5, 12, 13, 14, 14], rows)
    rows = []
    for r in A["sensitivity"]:
        rows.append([r["title"], str(r["n"]), n(r["euclid"], 1), n(r["euclid_adj"], 1), n(r["manhattan_adj"], 1), n(r["loo_mmre"] * 100)])
    out["TABLE_SENS"] = table(["Склад бази", "Проєктів", "Евклід, k = 3", "Евклід, k = 3, з корекцією", "Манхеттен, k = 2, з корекцією", "MMRE останньої, %"], [34, 11, 12, 14, 16, 13], rows)
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
