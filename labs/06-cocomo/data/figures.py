"""Рисунки ПР6: вплив розміру на трудомісткість і тривалість, порівняння моделей."""

import json
from pathlib import Path

import matplotlib.pyplot as plt

HERE = Path(__file__).parent
OUT = HERE.parent / "docs" / "report" / "assets"
C = json.loads((HERE / "cocomo.json").read_text(encoding="utf-8"))
S = C["sweep"]
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True, "grid.alpha": 0.3, "figure.dpi": 300})
SERIES = [
    ("Базова, напіврозділений", [v for v in S["basic"]["Напіврозділений"]], "pm", "tm", "#bab0ac", "-"),
    ("Проміжна, напіврозділений", [v for v in S["inter"]["Напіврозділений"]], "pm", "tm", "#f58518", "-"),
    ("COCOMO II Early Design", S["early"], "pm", "tdev", "#4c78a8", "-"),
    ("COCOMO II Post-Architecture", S["post"], "pm", "tdev", "#54a24b", "-"),
    ("COCOMO II, усе номінальне, новизна висока", S["post_nom"], "pm", "tdev", "#e45756", "--"),
]


def size_effect() -> None:
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(8.5, 3.8))
    for name, rows, k1, k2, color, ls in SERIES:
        a1.plot(S["sizes"], [r[k1] for r in rows], ls, marker="o", ms=3, color=color, label=name)
        a2.plot(S["sizes"], [r[k2] for r in rows], ls, marker="o", ms=3, color=color)
    for a in (a1, a2):
        a.set_xlabel("Розмір, KSLOC")
        a.axvline(C["size"], color="#555", lw=0.8, ls=":")
    a1.set_ylabel("Трудомісткість PM, людино-місяців")
    a2.set_ylabel("Тривалість TM, місяців")
    a1.legend(frameon=False, fontsize=7, loc="upper left")
    fig.tight_layout()
    fig.savefig(OUT / "01_size_effect.png")
    plt.close(fig)


def models() -> None:
    rows = [
        ("Базова", C["basic"]["Напіврозділений"]["pm"], "#bab0ac"),
        ("Проміжна", C["intermediate"]["types"]["Напіврозділений"]["pm"], "#f58518"),
        ("COCOMO II Early, 72.0 KSLOC", C["early_loc"]["pm"], "#4c78a8"),
        ("COCOMO II Post, 72.0 KSLOC", C["post_loc"]["pm"], "#54a24b"),
        ("COCOMO II Early, 50.1 KSLOC", C["early"]["pm"], "#9ecae1"),
        ("COCOMO II Post, 50.1 KSLOC", C["post"]["pm"], "#a1d99b"),
    ]
    fig, ax = plt.subplots(figsize=(7.5, 3.4))
    ys = range(len(rows))
    ax.barh(list(ys), [r[1] for r in rows], color=[r[2] for r in rows])
    for y, r in zip(ys, rows):
        ax.text(r[1] + 5, y, f"{r[1]:.0f}", va="center", fontsize=9)
    ax.set_yticks(list(ys), [r[0] for r in rows])
    ax.invert_yaxis()
    ax.set_xlabel("Трудомісткість, людино-місяців")
    ax.set_xlim(0, 450)
    ax.grid(axis="y", visible=False)
    fig.tight_layout()
    fig.savefig(OUT / "02_models.png")
    plt.close(fig)


if __name__ == "__main__":
    size_effect()
    models()
    print("ok")
