"""Економічні розрахунки за розміром у LOC: Effort, Schedule, Cost для Shopizer і порівняння рівнів мов.

Запуск: python3 data/economy.py   (після measure.py)
Результат: data/economy.json
"""

import json
from pathlib import Path

HERE = Path(__file__).parent
LOC = json.loads((HERE / "loc.json").read_text(encoding="utf-8"))

SALARY_USD = 2500  # медіана Middle (усі мови), DOU, літо 2026
USD_UAH = 45.666  # офіційний курс НБУ на 04.11.2026

# Boehm B. W. Software Engineering Economics, 1981: базова модель COCOMO
TYPES = {
    "Органічний": dict(a=2.4, b=1.05, c=2.5, d=0.38),
    "Напіврозділений": dict(a=3.0, b=1.12, c=2.5, d=0.35),
    "Вбудований": dict(a=3.6, b=1.20, c=2.5, d=0.32),
}

# Jones C. Software Economics and Function Point Metrics, 2017, табл. 16: логічні оператори на один FP
LANGS = {
    "Асемблер": dict(level=1.0, sloc_per_fp=320.00, loc_month=690, fp_month=2.16),
    "C": dict(level=2.5, sloc_per_fp=128.00, loc_month=643, fp_month=5.02),
    "Java": dict(level=6.0, sloc_per_fp=53.33, loc_month=554, fp_month=10.40),
    "C#": dict(level=6.25, sloc_per_fp=51.20, loc_month=549, fp_month=10.72),
}
# QSM Function Point Languages Table v5.0: SLOC на один FP (середнє, медіана, мін., макс.)
QSM = {"Java": (53, 53, 14, 134), "C#": (54, 59, 29, 70), "C": (97, 99, 39, 333)}


def cocomo(kloc: float, t: dict) -> dict:
    effort = t["a"] * kloc ** t["b"]
    schedule = t["c"] * effort ** t["d"]
    cost_usd = effort * SALARY_USD
    return {
        "kloc": kloc,
        "effort_pm": effort,
        "schedule_months": schedule,
        "team": effort / schedule,
        "cost_usd": cost_usd,
        "cost_uah": cost_usd * USD_UAH,
        "cost_per_loc_usd": cost_usd / (kloc * 1000),
        "loc_per_pm": kloc * 1000 / effort,
    }


def main() -> None:
    main_ = LOC["java_main"]
    test = LOC["java_test"]
    sizes = {
        "Фізичні рядки": main_["physical"] / 1000,
        "Рядки коду (cloc)": main_["code"] / 1000,
        "Логічні оператори": main_["logical"] / 1000,
    }
    base_kloc = sizes["Рядки коду (cloc)"]
    out = {
        "salary_usd": SALARY_USD,
        "usd_uah": USD_UAH,
        "sizes_kloc": sizes,
        "comment_ratio": main_["comment"] / main_["code"],
        "lloc_to_code": main_["logical"] / main_["code"],
    }
    out["by_type"] = {n: cocomo(base_kloc, t) for n, t in TYPES.items()}
    semi = TYPES["Напіврозділений"]
    out["by_size_definition"] = {n: cocomo(k, semi) for n, k in sizes.items()}
    out["with_tests"] = cocomo((main_["code"] + test["code"]) / 1000, semi)

    # Зворотний розрахунок (backfiring) в FP за логічними операторами і переказ на інші мови
    fp = main_["logical"] / LANGS["Java"]["sloc_per_fp"]
    out["backfired_fp"] = fp
    out["lang_effect"] = {}
    for name, l in LANGS.items():
        lloc = fp * l["sloc_per_fp"]
        kloc = (
            lloc * (main_["code"] / main_["logical"]) / 1000
        )  # рядки коду пропорційно логічним
        r = cocomo(kloc, semi)
        r.update(
            lloc=lloc,
            level=l["level"],
            sloc_per_fp=l["sloc_per_fp"],
            loc_month_jones=l["loc_month"],
            fp_month_jones=l["fp_month"],
            cost_per_fp_usd=r["cost_usd"] / fp,
        )
        out["lang_effect"][name] = r
    (HERE / "economy.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(
        "розміри, KLOC:",
        {k: round(v, 3) for k, v in sizes.items()},
        "F =",
        round(out["comment_ratio"], 3),
    )
    for n, r in out["by_type"].items():
        print(
            f"{n:16} E={r['effort_pm']:7.1f} T={r['schedule_months']:5.1f} N={r['team']:5.1f} ${r['cost_usd']:>10,.0f} {r['cost_uah']:>13,.0f} грн  ${r['cost_per_loc_usd']:.2f}/LOC  {r['loc_per_pm']:.0f} LOC/PM"
        )
    for n, r in out["by_size_definition"].items():
        print(
            f"{n:20} E={r['effort_pm']:7.1f} T={r['schedule_months']:5.1f} ${r['cost_usd']:>10,.0f}"
        )
    t = out["with_tests"]
    print(
        f"з тестами {t['kloc']:.3f} KLOC E={t['effort_pm']:.1f} T={t['schedule_months']:.1f} ${t['cost_usd']:,.0f}"
    )
    print("FP за зворотним розрахунком:", round(fp, 1))
    for n, r in out["lang_effect"].items():
        print(
            f"{n:9} lvl {r['level']:<5} lloc {r['lloc']:9,.0f} kloc {r['kloc']:7.1f} E={r['effort_pm']:7.1f} ${r['cost_usd']:>11,.0f} ${r['cost_per_loc_usd']:.2f}/LOC ${r['cost_per_fp_usd']:,.0f}/FP"
        )


if __name__ == "__main__":
    main()
