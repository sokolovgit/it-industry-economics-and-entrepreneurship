"""report.src.md -> report.md: нумерація джерел [@Key] і вставка таблиць із результатів обчислень."""

import csv
import json
import re
from pathlib import Path

HERE = Path(__file__).parent
REPORT = HERE.parent / "docs" / "report"
D = "дата звернення: 04.11.2026"
LV = {"L": "Низький", "A": "Середній", "H": "Високий"}
W = {"ILF": (7, 10, 15), "EIF": (5, 7, 10), "EI": (3, 4, 6), "EO": (4, 5, 7), "EQ": (3, 4, 6)}

SOURCES = {
    "Shopizer": f"Shopizer: Java open source e-commerce software. URL: https://github.com/shopizer-ecommerce/shopizer, коміт 6a4a0a6 від 23.03.2025 ({D}).",
    "IFPUG": "Function Point Counting Practices Manual, Release 4.3.1. International Function Point Users Group, 2010.",
    "ISO20926": "ISO/IEC 20926:2009. Software and systems engineering – Software measurement – IFPUG functional size measurement method 2009. Geneva : ISO, 2009.",
    "Jones2017": f"Jones C. Software Economics and Function Point Metrics: Thirty years of IFPUG Progress, версія 10.0. Namcook Analytics, 14.04.2017. URL: https://www.ifpug.org/wp-content/uploads/2017/04/IYSM.-Thirty-years-of-IFPUG.-Software-Economics-and-Function-Point-Metrics-Capers-Jones.pdf ({D}).",
    "Boehm1981": "Boehm B. W. Software Engineering Economics. Englewood Cliffs, NJ : Prentice-Hall, 1981. 767 p.",
    "DOU2026": f"Зарплати українських розробників – літо 2026. DOU. 13.07.2026. URL: https://dou.ua/lenta/articles/salary-report-devs-summer-2026/ ({D}).",
    "NBU": f"Офіційний курс гривні щодо іноземних валют на 04.11.2026: долар США 45.666 UAH. Національний банк України. URL: https://bank.gov.ua/NBUStatService/v1/statdirectory/exchange?valcode=USD&date=20261104&json ({D}).",
}

GSC_NOTES = [
    "REST/HTTP, відправлення пошти, HTTP-виклики платіжних шлюзів і перевізників: більше одного протоколу",
    "Застосунок відокремлений від адміністративного інтерфейсу і вітрини, кеш і сховища файлів – окремі компоненти",
    "Використано кешування, жорстких вимог до часу відповіді немає",
    "Працює на стандартній JVM, обмежень немає",
    "Інтернет-магазин, піки навантаження під час розпродажів, спеціальних рішень немає",
    "Усі транзакції виконуються інтерактивно через API",
    "Підтримка кількох мов і валют, повідомлення про помилки валідації",
    "Половина транзакцій (EI) змінює дані онлайн",
    "Безпека (JWT, ролі), розрахунок цін, податків і доставки",
    "API використовується різними вітринами, модулі оплати і доставки замінні",
    "Збірка Maven, Docker, схема бази даних створюється автоматично",
    "Керування кешем через API, автоматичного відновлення немає",
    "Кілька СУБД (H2, MySQL), сховища (локальне, AWS, GCP), кілька магазинів в одній установці",
    "Настроювані атрибути, варіанти товарів, опції клієнта, інтеграційні модулі",
]


def esc(s: str) -> str:
    return s.replace("|", "\\|").replace("$", "\\$")


def table(header: list[str], widths: list[int], rows: list[list[str]]) -> str:
    lines = ["| " + " | ".join(header) + " |", "| " + " | ".join("-" * w for w in widths) + " |"]
    lines += ["| " + " | ".join(r) + " |" for r in rows]
    return "\n".join(lines)


def tables() -> dict[str, str]:
    ilf = json.loads((HERE / "ilf.json").read_text(encoding="utf-8"))
    fpa = json.loads((HERE / "fpa.json").read_text(encoding="utf-8"))
    out = {}
    rows = []
    for i, (name, v) in enumerate(ilf["ilf"].items(), 1):
        rows.append([str(i), name, ", ".join(v["entities"]), str(v["ret"]), str(v["det"]), LV[v["level"]], str(W["ILF"]["LAH".index(v["level"])])])
    out["TABLE_ILF"] = table(["№", "Файл", "Сутності (RET)", "RET", "DET", "Складність", "UFP"], [5, 22, 34, 6, 6, 19, 8], rows)
    rows = [[n, v["note"], str(v["ret"]), str(v["det"]), LV[v["level"]], str(W["EIF"]["LAH".index(v["level"])])] for n, v in ilf["eif"].items()]
    out["TABLE_EIF"] = table(["Файл", "Зміст", "RET", "DET", "Складність", "UFP"], [26, 34, 7, 7, 19, 8], rows)
    rows = []
    for comp, name in (("EI", "Зовнішні входи (EI)"), ("EO", "Зовнішні виходи (EO)"), ("EQ", "Зовнішні запити (EQ)"), ("ILF", "Внутрішні логічні файли (ILF)"), ("EIF", "Зовнішні інтерфейсні файли (EIF)")):
        c = fpa["counts"][comp]
        cells = [f"{c[lv]} × {W[comp]['LAH'.index(lv)]} = {c[lv] * W[comp]['LAH'.index(lv)]}" for lv in "LAH"]
        rows.append([name, *cells, str(fpa["subtotals"][comp])])
    rows.append(["Разом", "", "", "", str(fpa["ufp"])])
    out["TABLE_UFP"] = table(["Компонент", "Низький", "Середній", "Високий", "Разом"], [34, 16, 16, 16, 10], rows)
    rows = [[str(i), n, str(v), GSC_NOTES[i - 1]] for i, (n, v) in enumerate(fpa["gsc"].items(), 1)]
    rows.append(["", "Разом (TDI)", str(fpa["tdi"]), ""])
    out["TABLE_GSC"] = table(["№", "Характеристика", "Оцінка", "Обґрунтування"], [5, 26, 10, 58], rows)
    rows = []
    for i, r in enumerate(csv.DictReader(open(HERE / "transactions.csv", encoding="utf-8")), 1):
        path = r["path"].replace("/", "/​")
        rows.append([str(i), r["type"], f"{r['http']} {esc(path)}", r["ftr"], r["det"], LV[r["level"]][:3] + ".", r["ufp"]])
    out["TABLE_TRANS"] = table(["№", "Тип", "Запит", "FTR", "DET", "Склад.", "UFP"], [6, 7, 54, 7, 7, 10, 7], rows)
    z = "/\u200b"
    manual = [
        ["DELETE /private/product/{id}", "EI, FTR 2, DET 2, 3 UFP", "EI, FTR 1, DET 2, 3 UFP", "FTR завищено, складність та сама"],
        ["GET /store/unique", "EQ, FTR 1, DET 1, 3 UFP", "EQ, FTR 1, DET 1, 3 UFP", "збігається"],
        ["POST /customer/login", "EQ, FTR 1, DET 1, 3 UFP", "EQ, FTR 1, DET 2 (логін, пароль), 3 UFP", "збігається"],
        ["PUT /private/products/{id}/reviews/{reviewid}", "EI, FTR 2, DET 10, 4 UFP", "EI, FTR 3 (відгук, клієнт, товар), 6 UFP", "FTR занижено, UFP на 2 менше"],
        ["PUT /private/category/{id}/move/{parent}", "EI, FTR 2, DET 3, 3 UFP", "EI, FTR 2, DET 3, 3 UFP", "збігається"],
        ["POST /private/modules/payment", "EI, FTR 3, DET 8, 6 UFP", "EI, FTR 2 (модуль, магазин), DET 6, 4 UFP", "FTR завищено (платіжні файли не використовуються), на 2 UFP більше"],
        ["GET /private/product/{sku}/price/{priceId}", "EQ, FTR 1, DET 14, 3 UFP", "EQ, FTR 1, DET 14, 3 UFP", "збігається після виправлення (тіло GET-запиту не рахується)"],
        ["POST /private/orders/{id}/capture", "EI, FTR 3, DET 2, 4 UFP", "метод повертає null, процесу немає, 0 UFP", "заглушка, на 4 UFP більше"],
        ["POST /private/file", "EI, FTR 1, DET 2, 3 UFP", "EI, FTR 1, DET 4 (назва, тип, вміст, відповідь), 3 UFP", "збігається"],
        ["GET /country", "EQ, FTR 2, DET 7, 4 UFP", "EQ, FTR 1 (довідники), DET 7, 3 UFP", "FTR завищено, на 1 UFP більше"],
    ]
    rows = [[esc(a.replace("/", z)), b, c, d] for a, b, c, d in manual]
    rows.append(["Разом", "36 UFP", "31 UFP", "програма більша на 5 UFP"])
    out["TABLE_MANUAL"] = table(["Транзакція", "Результат програми", "Вручну", "Висновок"], [32, 22, 26, 26], rows)
    return out


def main():
    src = (REPORT / "report.src.md").read_text(encoding="utf-8")
    for k, v in tables().items():
        src = src.replace(f"<!-- {k} -->", v)
    order: list[str] = []

    def num(key: str) -> str:
        if key not in SOURCES:
            raise SystemExit(f"невідоме джерело: {key}")
        if key not in order:
            order.append(key)
        return str(order.index(key) + 1)

    body = re.sub(
        r"\[@([\w,;\s@]+)\]",
        lambda m: "[" + ", ".join(num(k.strip().lstrip("@")) for k in re.split(r"[,;]", m.group(1))) + "]",
        src,
    )
    refs = "\n".join(f"{i}. {SOURCES[k]}" for i, k in enumerate(order, start=1))
    body = body.replace("<!-- SOURCES -->", refs)
    (REPORT / "report.md").write_text(body, encoding="utf-8")
    print(f"посилань: {len(order)}; не використано: {sorted(set(SOURCES) - set(order))}")


if __name__ == "__main__":
    main()
