"""report.src.md -> report.md: нумерація джерел [@Key] і вставка таблиць із результатів обчислень."""

import json
import re
from pathlib import Path

import cocomo as M

HERE = Path(__file__).parent
REPORT = HERE.parent / "docs" / "report"
D = "дата звернення: 04.11.2026"
RN = {"VL": "Дуже низький", "L": "Низький", "N": "Номінальний", "H": "Високий", "VH": "Дуже високий", "XH": "Критичний", "XL": "Дуже низький"}
RN2 = {"XL": "Дуже низький", "VL": "Низький", "L": "Нижче номіналу", "N": "Номінальний", "H": "Високий", "VH": "Дуже високий", "XH": "Критичний"}

SOURCES = {
    "Boehm1981": "Boehm B. W. Software Engineering Economics. Englewood Cliffs, NJ : Prentice-Hall, 1981. 767 p.",
    "CII": f"COCOMO II Model Definition Manual, Version 2.1. Center for Software Engineering, University of Southern California, 2000. URL: https://web.archive.org/web/2016/http://csse.usc.edu/csse/research/COCOMOII/cocomo2000.0/CII_modelman2000.0.pdf ({D}).",
    "Boehm2000": "Boehm B. W., Abts C., Brown A. W. et al. Software Cost Estimation with COCOMO II. Upper Saddle River, NJ : Prentice Hall, 2000. 544 p.",
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


def tables():
    C = json.loads((HERE / "cocomo.json").read_text(encoding="utf-8"))
    out = {}
    rows = [[t, n(v["pm"], 1), n(v["tm"], 1), n(v["staff"], 1), n(v["pm"] * C["salary"]), n(v["pm"] * C["salary"] * C["rate"] / 1e6, 1)] for t, v in C["basic"].items()]
    out["TABLE_BASIC"] = table(["Тип проєкту", "PM, людино-місяців", "TM, міс.", "Розробн.", "Вартість, \\$", "Вартість, млн грн"], [24, 16, 11, 15, 15, 14], rows)
    rows = []
    for name, ru, vals, r, why in M.INT_DRIVERS:
        v = vals[M.LEVELS6.index(r)]
        rows.append([f"{name} {ru}", RN[r], n(v, 2), why])
    rows.append(["EAF", "", n(C["intermediate"]["eaf"], 3), "добуток множників"])
    out["TABLE_INTDRV"] = table(["Фактор", "Рівень", "Значення", "Обґрунтування"], [22, 17, 15, 46], rows)
    rows = [[t, n(v["pm"], 1), n(v["tm"], 1), n(v["staff"], 1), n(v["pm"] * C["salary"]), n(v["pm"] * C["salary"] * C["rate"] / 1e6, 1)] for t, v in C["intermediate"]["types"].items()]
    out["TABLE_INTER"] = table(["Тип проєкту", "PM, людино-місяців", "TM, міс.", "Розробн.", "Вартість, \\$", "Вартість, млн грн"], [24, 16, 11, 15, 15, 14], rows)
    rows = [[f"{nm} {ru}", RN[r], n(vals[M.LEVELS6.index(r)], 2), why] for nm, ru, vals, r, why in M.SF]
    rows.append(["Разом ΣSF", "", n(C["sf"]["sum"], 2), f"E = 0.91 + 0.01 · {n(C['sf']['sum'], 2)} = {n(C['sf']['E'], 4)}"])
    out["TABLE_SF"] = table(["Фактор масштабу", "Рівень", "Значення", "Обґрунтування"], [26, 17, 15, 42], rows)
    rows = [[f"{nm} {ru}", RN2[r], n(vals[M.LEV7.index(r)], 2), why] for nm, ru, vals, r, why in M.EM_EARLY]
    out["TABLE_EARLY"] = table(["Множник", "Рівень", "Значення", "Обґрунтування"], [28, 17, 15, 40], rows + [["EM, добуток", "", n(C["early"]["em"], 3), ""]])
    rows = [[f"{nm} {ru}", RN[r], n(vals[M.LEVELS6.index(r)], 2), why] for nm, ru, vals, r, why in M.EM_POST]
    out["TABLE_POST"] = table(["Множник", "Рівень", "Значення", "Обґрунтування"], [28, 17, 15, 40], rows + [["EM, добуток", "", n(C["post"]["em"], 3), ""]])
    rows = []
    for title, k in (("Early Design", "early"), ("Post-Architecture", "post")):
        for sz, kk in ((f"{n(C['size_logical'], 1)} (логічні оператори)", k), (f"{n(C['size'], 1)} (рядки коду)", k + "_loc")):
            v = C[kk]
            rows.append([title, sz, n(v["pm"], 1), n(v["tdev"], 1), n(v["staff"], 1), n(v["cost_usd"]), n(v["cost_uah"] / 1e6, 1)])
    out["TABLE_II"] = table(["Модель", "Розмір, KSLOC", "PM", "TM", "Розробників", "Вартість, \\$", "Вартість, млн грн"], [22, 22, 9, 8, 17, 13, 14], rows)
    sw = C["sweep"]
    def sweep(key):
        header = ["Розмір, KSLOC", "Базова", "Проміжна", "Early Design", "Post-Architecture", "Номінальна, висока новизна"]
        rows = []
        for i, s in enumerate(sw["sizes"]):
            f = (lambda v: n(v[key if key in v else "tdev"], 1))
            rows.append([str(s), n(sw["basic"]["Напіврозділений"][i][key], 1), n(sw["inter"]["Напіврозділений"][i][key], 1),
                         n(sw["early"][i]["pm" if key == "pm" else "tdev"], 1), n(sw["post"][i]["pm" if key == "pm" else "tdev"], 1), n(sw["post_nom"][i]["pm" if key == "pm" else "tdev"], 1)])
        return table(header, [14, 14, 14, 15, 18, 21], rows)
    out["TABLE_SWEEP_PM"] = sweep("pm")
    out["TABLE_SWEEP_TM"] = sweep("tm")
    rows = [[k, n(v["pm"], 1), n(v.get("tm", v.get("tdev")), 1)] for k, v in C["novel"].items()]
    out["TABLE_NOVEL"] = table(["Модель", "PM, людино-місяців", "TM, місяців"], [44, 22, 20], rows)
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
