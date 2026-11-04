"""Рисунки звіту: склад коду за модулями, залежність трудомісткості від розміру, мови за рівнем.

Запуск: uv run --no-project --with matplotlib python data/figures.py   (після measure.py і economy.py)
"""

import json
from pathlib import Path

import matplotlib.pyplot as plt

HERE = Path(__file__).parent
OUT = HERE.parent / "docs" / "report" / "assets"
LOC = json.loads((HERE / "loc.json").read_text(encoding="utf-8"))
ECO = json.loads((HERE / "economy.json").read_text(encoding="utf-8"))

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
C_CODE, C_COMM, C_BLANK = "#4c78a8", "#f58518", "#bab0ac"
TYPE_COLORS = {
    "Органічний": "#54a24b",
    "Напіврозділений": "#4c78a8",
    "Вбудований": "#e45756",
}


def modules() -> None:
    names = ["sm-core-model", "sm-core-modules", "sm-core", "sm-shop-model", "sm-shop"]
    rows = [LOC["modules"][f"{n}/main"] for n in names]
    fig, ax = plt.subplots(figsize=(7.5, 3.6))
    y = range(len(names))
    code = [r["code"] / 1000 for r in rows]
    comm = [r["comment"] / 1000 for r in rows]
    blank = [r["blank"] / 1000 for r in rows]
    ax.barh(y, code, color=C_CODE, label="Рядки коду")
    ax.barh(y, comm, left=code, color=C_COMM, label="Коментарі")
    ax.barh(
        y,
        blank,
        left=[a + b for a, b in zip(code, comm)],
        color=C_BLANK,
        label="Порожні рядки",
    )
    for i, r in enumerate(rows):
        total = (r["code"] + r["comment"] + r["blank"]) / 1000
        ax.text(total + 0.4, i, f"{total:.1f}", va="center", fontsize=9)
    ax.set_yticks(list(y), names)
    ax.invert_yaxis()
    ax.set_xlabel("Тисяч рядків, Java (src/main)")
    ax.set_xlim(0, 52)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.22), ncol=3, frameon=False)
    ax.grid(axis="y", visible=False)
    fig.tight_layout()
    fig.savefig(OUT / "01_modules.png")
    plt.close(fig)


def effort_curve() -> None:
    from_ = [k / 2 for k in range(20, 201)]
    fig, ax = plt.subplots(figsize=(7.5, 3.8))
    types = {
        "Органічний": (2.4, 1.05),
        "Напіврозділений": (3.0, 1.12),
        "Вбудований": (3.6, 1.20),
    }
    for name, (a, b) in types.items():
        ax.plot(from_, [a * k**b for k in from_], color=TYPE_COLORS[name], label=name)
    kloc = ECO["sizes_kloc"]["Рядки коду (cloc)"]
    ax.axvline(kloc, color="#333", ls="--", lw=1)
    ax.text(
        kloc - 1, 700, f"Shopizer\n{kloc:.1f} KLOC", ha="right", va="top", fontsize=9
    )
    for name, r in ECO["by_type"].items():
        ax.plot([kloc], [r["effort_pm"]], "o", color=TYPE_COLORS[name])
        ax.annotate(
            f"{r['effort_pm']:.0f}",
            (kloc, r["effort_pm"]),
            textcoords="offset points",
            xytext=(6, -3),
            fontsize=9,
        )
    ax.set_xlabel("Розмір, KLOC")
    ax.set_ylabel("Трудомісткість, людино-місяців")
    ax.set_xlim(10, 100)
    ax.set_ylim(0, 800)
    ax.legend(frameon=False, loc="upper left")
    fig.tight_layout()
    fig.savefig(OUT / "02_effort.png")
    plt.close(fig)


def languages() -> None:
    langs = ["Асемблер", "C", "Java", "C#"]
    eff = ECO["lang_effect"]
    colors = ["#bab0ac", "#e45756", "#4c78a8", "#54a24b"]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(8, 3.6))
    kloc = [eff[l]["lloc"] / 1000 for l in langs]
    a1.bar(langs, kloc, color=colors)
    for i, v in enumerate(kloc):
        a1.text(i, v + 5, f"{v:.0f}", ha="center", fontsize=9)
    a1.set_ylabel("Тисяч логічних операторів")
    a1.set_title(f"Однаковий функціонал ({ECO['backfired_fp']:.0f} FP)", fontsize=10)
    a1.set_ylim(0, 340)
    a1.grid(axis="x", visible=False)

    w = 0.38
    xs = range(len(langs))
    loc_m = [eff[l]["loc_month_jones"] for l in langs]
    fp_m = [eff[l]["fp_month_jones"] for l in langs]
    a2.bar([x - w / 2 for x in xs], loc_m, w, color="#f58518", label="LOC за місяць")
    a2.set_ylabel("LOC за місяць")
    a2.set_ylim(0, 800)
    a2.set_xticks(list(xs), langs)
    a2.grid(axis="x", visible=False)
    a3 = a2.twinx()
    a3.bar([x + w / 2 for x in xs], fp_m, w, color="#4c78a8", label="FP за місяць")
    a3.set_ylabel("FP за місяць")
    a3.set_ylim(0, 16)
    a3.spines["right"].set_visible(True)
    a3.grid(False)
    h1, l1 = a2.get_legend_handles_labels()
    h2, l2 = a3.get_legend_handles_labels()
    a2.legend(h1 + h2, l1 + l2, frameon=False, loc="upper center", fontsize=8, ncol=2)
    a2.set_title("Продуктивність за Джонсом", fontsize=10)
    fig.tight_layout()
    fig.savefig(OUT / "03_languages.png")
    plt.close(fig)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    modules()
    effort_curve()
    languages()
    print("ok")
