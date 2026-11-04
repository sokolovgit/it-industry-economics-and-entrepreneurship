"""COCOMO: базова і проміжна моделі, COCOMO II (Early Design і Post-Architecture) для Shopizer.

Запуск: python3 data/cocomo.py   (після ПР2)
Результат: data/cocomo.json
"""

import json
import math
from pathlib import Path

HERE = Path(__file__).parent
PR2 = HERE.parent.parent / "02-loc-metrics" / "data"
ECO2 = json.loads((PR2 / "economy.json").read_text(encoding="utf-8"))
LOC = json.loads((PR2 / "loc.json").read_text(encoding="utf-8"))
SIZE = ECO2["sizes_kloc"]["Рядки коду (cloc)"]  # 72.016 KLOC: розмір для базової і проміжної моделей і порівняння
SIZE_LOGICAL = ECO2["sizes_kloc"]["Логічні оператори"]  # 50.133 KSLOC: одиниця COCOMO II
SALARY, RATE = ECO2["salary_usd"], ECO2["usd_uah"]

# ---- Базова і проміжна моделі (Boehm, 1981) ----
BASIC = {"Органічний": (2.4, 1.05, 2.5, 0.38), "Напіврозділений": (3.0, 1.12, 2.5, 0.35), "Вбудований": (3.6, 1.20, 2.5, 0.32)}
INTER = {"Органічний": (3.2, 1.05), "Напіврозділений": (3.0, 1.12), "Вбудований": (2.8, 1.20)}
LEVELS6 = ["VL", "L", "N", "H", "VH", "XH"]
INT_DRIVERS = [  # назва, ваги за рівнями VL..XH (None – n/a), оцінка Shopizer, обґрунтування
    ("RELY", "Необхідна надійність", [0.75, 0.88, 1.00, 1.15, 1.40, None], "H", "помилки призводять до помітних фінансових втрат: замовлення і платежі"),
    ("DATA", "Розмір бази даних", [None, 0.94, 1.00, 1.08, 1.16, None], "N", "обсяг бази залежить від магазину, даних немає"),
    ("CPLX", "Складність продукту", [0.70, 0.85, 1.00, 1.15, 1.30, 1.65], "H", "розрахунок цін, податків, доставки, пакування, безпека"),
    ("TIME", "Обмеження швидкодії", [None, None, 1.00, 1.11, 1.30, 1.66], "N", "використання процесора не обмежено вимогами"),
    ("STOR", "Обмеження пам'яті", [None, None, 1.00, 1.06, 1.21, 1.56], "N", "обмежень пам'яті немає"),
    ("VIRT", "Нестійкість віртуальної машини", [None, 0.87, 1.00, 1.15, 1.30, None], "N", "JVM і Spring Boot змінюються рідко"),
    ("TURN", "Час відновлення", [None, 0.87, 1.00, 1.07, 1.15, None], "N", "особливих вимог немає"),
    ("ACAP", "Здібності аналітиків", [1.46, 1.19, 1.00, 0.86, 0.71, None], "N", "склад команди невідомий, прийнято середній рівень"),
    ("AEXP", "Досвід у предметній області", [1.29, 1.13, 1.00, 0.91, 0.82, None], "N", "прийнято середній рівень"),
    ("PCAP", "Здібності програмістів", [1.42, 1.17, 1.00, 0.86, 0.70, None], "N", "прийнято середній рівень"),
    ("VEXP", "Досвід з віртуальною машиною", [1.21, 1.10, 1.00, 0.90, None, None], "N", "прийнято середній рівень"),
    ("LEXP", "Досвід з мовою програмування", [1.14, 1.07, 1.00, 0.95, None, None], "N", "прийнято середній рівень"),
    ("MODP", "Сучасні методи розробки", [1.24, 1.10, 1.00, 0.91, 0.82, None], "H", "код-рев'ю, модульна архітектура, шаблони Spring"),
    ("TOOL", "Інструменти розробки", [1.24, 1.10, 1.00, 0.91, 0.83, None], "H", "Maven, Docker, середовище розробки і CI"),
    ("SCED", "Вимоги до графіка", [1.23, 1.08, 1.00, 1.04, 1.10, None], "N", "графік не стиснуто"),
]

# ---- COCOMO II.2000 (USC, Model Definition Manual 2.1) ----
A, B, C, D = 2.94, 0.91, 3.67, 0.28
SF = [  # назва, значення VL..XH, оцінка Shopizer, обґрунтування
    ("PREC", "Передбачуваність", [6.20, 4.96, 3.72, 2.48, 1.24, 0.00], "H", "типовий застосунок електронної комерції, домен добре відомий"),
    ("FLEX", "Гнучкість розробки", [5.07, 4.05, 3.04, 2.03, 1.01, 0.00], "VH", "відкритий проєкт, вимоги виконуються з частковою відповідністю (some conformity)"),
    ("RESL", "Розв'язання ризиків і архітектура", [7.07, 5.65, 4.24, 2.83, 1.41, 0.00], "H", "модульна архітектура з п'яти модулів, ризики розв'язано переважно (75%)"),
    ("TEAM", "Згуртованість команди", [5.48, 4.38, 3.29, 2.19, 1.10, 0.00], "H", "розподілена спільнота, взаємодія в цілому кооперативна"),
    ("PMAT", "Зрілість процесу", [7.80, 6.24, 4.68, 3.12, 1.56, 0.00], "N", "відповідає другому рівню CMM"),
]
LEV7 = ["XL", "VL", "L", "N", "H", "VH", "XH"]
EM_POST = [  # назва, значення VL..XH (6 рівнів: VL,L,N,H,VH,XH), оцінка, обґрунтування
    ("RELY", "Надійність", [0.82, 0.92, 1.00, 1.10, 1.26, None], "H", "помилки призводять до помітних фінансових втрат"),
    ("DATA", "Розмір бази даних", [None, 0.90, 1.00, 1.14, 1.28, None], "N", "обсяг бази залежить від магазину, даних немає"),
    ("CPLX", "Складність продукту", [0.73, 0.87, 1.00, 1.17, 1.34, 1.74], "H", "розрахунок цін, податків, доставки, безпека"),
    ("RUSE", "Розробка для повторного використання", [None, 0.95, 1.00, 1.07, 1.15, 1.24], "H", "платформа, яку підключають різні вітрини"),
    ("DOCU", "Документація", [0.81, 0.91, 1.00, 1.11, 1.23, None], "N", "є документація API, інакше потреб немає"),
    ("TIME", "Обмеження часу виконання", [None, None, 1.00, 1.11, 1.29, 1.63], "N", "обмежень немає"),
    ("STOR", "Обмеження пам'яті", [None, None, 1.00, 1.05, 1.17, 1.46], "N", "обмежень немає"),
    ("PVOL", "Нестійкість платформи", [None, 0.87, 1.00, 1.15, 1.30, None], "N", "платформа змінюється рідко"),
    ("ACAP", "Здібності аналітиків", [1.42, 1.19, 1.00, 0.85, 0.71, None], "N", "склад команди невідомий"),
    ("PCAP", "Здібності програмістів", [1.34, 1.15, 1.00, 0.88, 0.76, None], "N", "склад команди невідомий"),
    ("PCON", "Стабільність персоналу", [1.29, 1.12, 1.00, 0.90, 0.81, None], "N", "дані відсутні"),
    ("APEX", "Досвід у предметній області", [1.22, 1.10, 1.00, 0.88, 0.81, None], "N", "склад команди невідомий"),
    ("PLEX", "Досвід з платформою", [1.19, 1.09, 1.00, 0.91, 0.85, None], "N", "склад команди невідомий"),
    ("LTEX", "Досвід з мовою та інструментами", [1.20, 1.09, 1.00, 0.91, 0.84, None], "N", "склад команди невідомий"),
    ("TOOL", "Інструменти", [1.17, 1.09, 1.00, 0.90, 0.78, None], "H", "Maven, Docker, середовище розробки і CI"),
    ("SITE", "Розподіленість розробки", [1.22, 1.09, 1.00, 0.93, 0.86, 0.80], "L", "учасники розподілені, зв'язок через мережу"),
    ("SCED", "Графік розробки", [1.43, 1.14, 1.00, 1.00, 1.00, None], "N", "графік не стиснуто"),
]
# Early Design: рівні XL, VL, L, N, H, VH, XH
EM_EARLY = [
    ("PERS", "Здібності персоналу", [2.12, 1.62, 1.26, 1.00, 0.83, 0.63, 0.50], "N", "склад команди невідомий"),
    ("RCPX", "Надійність і складність продукту", [0.49, 0.60, 0.83, 1.00, 1.33, 1.91, 2.72], "H", "помітні фінансові втрати при помилках, висока складність"),
    ("RUSE", "Повторне використання", [None, None, 0.95, 1.00, 1.07, 1.15, 1.24], "H", "платформа для різних вітрин"),
    ("PDIF", "Складність платформи", [None, None, 0.87, 1.00, 1.29, 1.81, 2.61], "N", "стандартна JVM, обмежень немає"),
    ("PREX", "Досвід персоналу", [1.59, 1.33, 1.22, 1.00, 0.87, 0.74, 0.62], "N", "склад команди невідомий"),
    ("FCIL", "Засоби і розподіленість", [1.43, 1.30, 1.10, 1.00, 0.87, 0.73, 0.62], "N", "TOOL високий, SITE низький, сума оцінок 6 – номінальний рівень"),
    ("SCED", "Графік розробки", [None, 1.43, 1.14, 1.00, 1.00, 1.00, None], "N", "графік не стиснуто"),
]
# Висока новизна, номінальна складність: усе номінальне, PREC дуже низький
NOVEL_SF = {"PREC": "VL", "FLEX": "N", "RESL": "N", "TEAM": "N", "PMAT": "N"}


def idx(levels, lv):
    return levels.index(lv)


def sf_sum(ratings):
    return sum(row[2][idx(LEVELS6, ratings[row[0]])] for row in SF)


def cocomo2(size, sf_ratings, em_values):
    s = sf_sum(sf_ratings)
    e = B + 0.01 * s
    em_prod = math.prod(v for k, v in em_values.items() if k != "SCED")
    sced = em_values.get("SCED", 1.0)
    pm_ns = A * size**e * em_prod
    pm = pm_ns * sced
    f = D + 0.2 * (e - B)
    tdev = C * pm_ns**f * (1.0 if sced == 1 else sced)  # SCED% у номіналі 100%
    return {"size": size, "sf": s, "E": e, "F": f, "em": math.prod(em_values.values()), "pm": pm, "tdev": tdev, "staff": pm / tdev}


def post_values(ratings):
    return {r[0]: r[2][idx(LEVELS6, ratings[r[0]])] for r in EM_POST}


def early_values(ratings):
    return {r[0]: r[2][idx(LEV7, ratings[r[0]])] for r in EM_EARLY}


def main() -> None:
    out = {"size": SIZE, "size_logical": SIZE_LOGICAL, "salary": SALARY, "rate": RATE}

    # Базова модель
    out["basic"] = {}
    for t, (a, b, c, d) in BASIC.items():
        e = a * SIZE**b
        tm = c * e**d
        out["basic"][t] = {"pm": e, "tm": tm, "staff": e / tm}

    # Проміжна модель: EAF для Shopizer
    eaf = math.prod(d[2][idx(LEVELS6, d[3])] for d in INT_DRIVERS)
    out["intermediate"] = {"eaf": eaf, "types": {}}
    for t, (a, b) in INTER.items():
        e = a * SIZE**b * eaf
        tm = BASIC[t][2] * e ** BASIC[t][3]
        out["intermediate"]["types"][t] = {"pm": e, "tm": tm, "staff": e / tm}

    # COCOMO II для Shopizer
    sf_r = {r[0]: r[3] for r in SF}
    post_r = {r[0]: r[3] for r in EM_POST}
    early_r = {r[0]: r[3] for r in EM_EARLY}
    out["sf"] = {"sum": sf_sum(sf_r), "E": B + 0.01 * sf_sum(sf_r)}
    out["early"] = cocomo2(SIZE_LOGICAL, sf_r, early_values(early_r))
    out["post"] = cocomo2(SIZE_LOGICAL, sf_r, post_values(post_r))
    out["early_loc"] = cocomo2(SIZE, sf_r, early_values(early_r))
    out["post_loc"] = cocomo2(SIZE, sf_r, post_values(post_r))

    # Вплив розміру
    sizes = [25, 50, 75, 100, 150, 200]
    nom_post = {r[0]: 1.0 for r in EM_POST}
    nom_early = {r[0]: 1.0 for r in EM_EARLY}
    out["sweep"] = {"sizes": sizes, "basic": {}, "inter": {}, "early": [], "post": [], "early_nom": [], "post_nom": []}
    for t, (a, b, c, d) in BASIC.items():
        out["sweep"]["basic"][t] = [{"pm": a * s**b, "tm": c * (a * s**b) ** d} for s in sizes]
    for t, (a, b) in INTER.items():
        out["sweep"]["inter"][t] = [{"pm": a * s**b * eaf, "tm": BASIC[t][2] * (a * s**b * eaf) ** BASIC[t][3]} for s in sizes]
    for s in sizes:
        out["sweep"]["early"].append(cocomo2(s, sf_r, early_values(early_r)))
        out["sweep"]["post"].append(cocomo2(s, sf_r, post_values(post_r)))
        out["sweep"]["early_nom"].append(cocomo2(s, NOVEL_SF, nom_early))
        out["sweep"]["post_nom"].append(cocomo2(s, NOVEL_SF, nom_post))

    # Однаковий розмір, номінальна складність, висока новизна
    nov = {}
    for t, (a, b, c, d) in BASIC.items():
        e = a * SIZE**b
        nov["Базова, " + t.lower()] = {"pm": e, "tm": c * e**d}
    for t, (a, b) in INTER.items():
        e = a * SIZE**b
        nov["Проміжна, " + t.lower()] = {"pm": e, "tm": BASIC[t][2] * e ** BASIC[t][3]}
    nov["COCOMO II Early Design"] = cocomo2(SIZE, NOVEL_SF, nom_early)
    nov["COCOMO II Post-Architecture"] = cocomo2(SIZE, NOVEL_SF, nom_post)
    out["novel"] = nov
    # перевірка реалізації за прикладом з керівництва: 100 KSLOC, E = 1.15 -> PM = 586.6, TDEV = 29.7
    e = 1.15
    pm = A * 100**e
    out["check"] = {"pm": pm, "tdev": C * pm ** (D + 0.2 * (e - B))}
    for k in ("early", "post", "early_loc", "post_loc"):
        v = out[k]
        v["cost_usd"] = v["pm"] * SALARY
        v["cost_uah"] = v["pm"] * SALARY * RATE
    (HERE / "cocomo.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("size", SIZE, SIZE_LOGICAL)
    for t, v in out["basic"].items():
        print("basic", t, round(v["pm"], 1), round(v["tm"], 1), round(v["staff"], 1))
    print("EAF", round(eaf, 4))
    for t, v in out["intermediate"]["types"].items():
        print("inter", t, round(v["pm"], 1), round(v["tm"], 1))
    print("SF", out["sf"])
    for k in ("early", "post", "early_loc", "post_loc"):
        v = out[k]
        print(k, {a: round(b, 3) for a, b in v.items()})
    print("check", out["check"])
    for k, v in out["novel"].items():
        print(k, round(v["pm"], 1), round(v.get("tm", v.get("tdev")), 1))


if __name__ == "__main__":
    main()
