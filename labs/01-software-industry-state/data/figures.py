"""Рисунки звіту: ефекти продуктивності, поширеність AI, якість коду, окупність, публікації за роками."""

import csv
import json
from collections import Counter
from pathlib import Path

import matplotlib.pyplot as plt

HERE = Path(__file__).parent
OUT = HERE.parent / "docs" / "report" / "assets"
IND = json.loads((HERE / "indicators.json").read_text(encoding="utf-8"))
STUDIES = list(csv.DictReader(open(HERE / "studies.csv", encoding="utf-8")))

plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "font.size": 10,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.alpha": 0.3,
        "figure.dpi": 300,
    }
)
GROUP = {
    "Рандомізований експеримент (лабораторний)": (
        "Лабораторні експерименти",
        "#4c78a8",
    ),
    "Рандомізований A/B-тест у банку": ("Лабораторні експерименти", "#4c78a8"),
    "Попередньо зареєстрований експеримент": ("Лабораторні експерименти", "#4c78a8"),
    "Три польові рандомізовані експерименти": ("Польові експерименти", "#54a24b"),
    "Рандомізований експеримент у компанії": ("Польові експерименти", "#54a24b"),
    "Рандомізований експеримент на реальних задачах": (
        "Польові експерименти",
        "#54a24b",
    ),
    "Спостережне дослідження з фіксованими ефектами": ("Спостережні дані", "#f58518"),
    "Квазіексперимент на даних GitHub": ("Спостережні дані", "#f58518"),
    "Різниці-в-різницях на репозиторіях": ("Спостережні дані", "#f58518"),
    "Лонгітюдний кейс": ("Спостережні дані", "#f58518"),
}


def save(fig, name):
    fig.tight_layout()
    fig.savefig(OUT / name, bbox_inches="tight")
    plt.close(fig)


def effects():
    rows = []
    for s in STUDIES:
        if s["benefit"] and s["design"] in GROUP:
            g, c = GROUP[s["design"]]
            rows.append(
                (
                    g,
                    c,
                    f"{s['code'][:-4]} {s['year']}: {s['metric'].split(';')[0].lower()}",
                    float(s["benefit"]),
                )
            )
    for v in IND["industry_effects"].values():
        rows.append(("Галузеві звіти", "#9d9d9d", v["label"], v["benefit"]))
    order = [
        "Лабораторні експерименти",
        "Польові експерименти",
        "Спостережні дані",
        "Галузеві звіти",
    ]
    rows.sort(key=lambda r: (order.index(r[0]), -r[3]))
    fig, ax = plt.subplots(figsize=(9.5, 5.6))
    y = list(range(len(rows)))[::-1]
    ax.barh(y, [r[3] for r in rows], color=[r[1] for r in rows])
    ax.set_yticks(y, [r[2] for r in rows], fontsize=8.5)
    for yi, r in zip(y, rows):
        ax.text(
            r[3] + (1 if r[3] >= 0 else -1),
            yi,
            f"{r[3]:+.1f}%",
            va="center",
            ha="left" if r[3] >= 0 else "right",
            fontsize=8.5,
        )
    ax.axvline(0, color="0.3", lw=1)
    ax.set_xlim(-30, 68)
    ax.set_xlabel(
        "ефект для продуктивності, % (додатне – швидше або більше результату)"
    )
    handles = [
        plt.Rectangle((0, 0), 1, 1, color=c)
        for c in ["#4c78a8", "#54a24b", "#f58518", "#9d9d9d"]
    ]
    ax.legend(handles, order, loc="lower right", fontsize=8.5)
    save(fig, "01_effects.png")


def adoption():
    so, fig = IND["stackoverflow"], plt.figure(figsize=(9.5, 3.8))
    ax1, ax2 = fig.add_subplot(1, 2, 1), fig.add_subplot(1, 2, 2)
    ax1.plot(so["years"], so["using"], "o-", label="Stack Overflow: використовують")
    ax1.plot(
        so["years"],
        so["using_or_planning"],
        "o--",
        label="Stack Overflow: використовують або планують",
    )
    ax1.plot(IND["dora"]["years"], IND["dora"]["ai_use"], "s-", label="DORA")
    ax1.plot(
        IND["jetbrains"]["years"], IND["jetbrains"]["ai_use"], "^-", label="JetBrains"
    )
    ax1.set_title("Частка розробників, що використовують AI, %", fontsize=10)
    ax1.set_xticks([2023, 2024, 2025, 2026])
    ax1.set_ylim(30, 100)
    ax1.legend(fontsize=7.5, loc="lower right")
    ax2.plot(
        so["years"], so["trust"], "o-", color="#54a24b", label="довіряють точності"
    )
    ax2.plot(so["years"], so["distrust"], "o-", color="#e45756", label="не довіряють")
    ax2.plot(
        so["years"],
        so["favorable"],
        "o--",
        color="#4c78a8",
        label="ставляться позитивно",
    )
    ax2.set_title("Ставлення до AI-інструментів (Stack Overflow), %", fontsize=10)
    ax2.set_xticks(so["years"])
    ax2.set_ylim(0, 90)
    ax2.legend(fontsize=7.5)
    save(fig, "02_adoption.png")


def gitclear():
    g = IND["gitclear"]
    fig, ax = plt.subplots(figsize=(8, 3.6))
    ax.plot(g["years"], g["moved"], "o-", label="переміщений код (рефакторинг)")
    ax.plot(g["years"], g["copy_pasted"], "o-", label="скопійований код")
    ax.plot(g["years"], g["churn"], "o-", label="код, переписаний протягом двох тижнів")
    ax.set_ylabel("частка змінених рядків, %")
    ax.set_xticks(g["years"])
    ax.legend(fontsize=8.5)
    save(fig, "03_gitclear.png")


def breakeven():
    sal, prices = IND["salary_usd_month"], IND["prices_usd_month"]
    names = list(prices)
    mid = [prices[n] / sal["middle_median"] * 100 for n in names]
    allm = [prices[n] / sal["all_median"] * 100 for n in names]
    fig, ax = plt.subplots(figsize=(9, 3.8))
    x = range(len(names))
    ax.bar(
        [i - 0.2 for i in x],
        mid,
        0.4,
        label=f"Middle, ${sal['middle_median']}/міс",
        color="#4c78a8",
    )
    ax.bar(
        [i + 0.2 for i in x],
        allm,
        0.4,
        label=f"медіана, ${sal['all_median']}/міс",
        color="#9ecae9",
    )
    for i, (a, b) in enumerate(zip(mid, allm)):
        ax.text(i - 0.2, a + 0.1, f"{a:.1f}", ha="center", fontsize=8)
        ax.text(i + 0.2, b + 0.1, f"{b:.1f}", ha="center", fontsize=8)
    ax.axhline(2.1, color="#f58518", ls="--", lw=1.2)
    ax.text(
        -0.45,
        2.25,
        "DORA 2024: +2.1%",
        color="#f58518",
        ha="left",
        fontsize=8,
    )
    ax.axhline(5.9, color="#54a24b", ls="--", lw=1.2)
    ax.text(
        -0.45,
        6.05,
        "Song 2024: +5.9%",
        color="#54a24b",
        ha="left",
        fontsize=8,
    )
    ax.set_xticks(list(x), [n.replace(" (", "\n(") for n in names], fontsize=8)
    ax.set_ylabel("потрібний приріст продуктивності, %")
    ax.set_ylim(0, 6.8)
    ax.legend(fontsize=8.5, loc="upper center")
    save(fig, "04_breakeven.png")


def by_year():
    rows = list(csv.DictReader(open(HERE / "records.csv", encoding="utf-8")))
    seen, years = set(), Counter()
    for r in rows:
        key = r["doi"].lower() or r["title"].lower()
        if key in seen:
            continue
        seen.add(key)
        years[int(r["year"])] += 1
    ys = sorted(y for y in years if 2022 <= y <= 2026)
    fig, ax = plt.subplots(figsize=(7, 3.2))
    ax.bar(ys, [years[y] for y in ys], color="#4c78a8")
    for y in ys:
        ax.text(y, years[y] + 3, str(years[y]), ha="center", fontsize=9)
    ax.set_ylabel("унікальних публікацій")
    ax.set_xticks(ys)
    save(fig, "05_by_year.png")
    return {y: years[y] for y in ys}


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    effects()
    adoption()
    gitclear()
    breakeven()
    print(by_year())
