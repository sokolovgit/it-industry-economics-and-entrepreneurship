"""Рисунки ПР4: Feature points проти функціональних точок, оцінки трудомісткості різними методами."""

import json
from pathlib import Path

import matplotlib.pyplot as plt

HERE = Path(__file__).parent
OUT = HERE.parent / "docs" / "report" / "assets"
P = json.loads((HERE / "points.json").read_text(encoding="utf-8"))
FPA = json.loads((HERE.parent.parent / "03-function-points" / "data" / "fpa.json").read_text(encoding="utf-8"))

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True, "grid.alpha": 0.3, "figure.dpi": 300})


def compare_components() -> None:
    c = P["fep"]["counts"]
    w = {"EI": 4, "EO": 5, "EQ": 4, "ILF": 7, "EIF": 7, "ALG": 3}
    comps = ["EI", "EO", "EQ", "ILF", "EIF", "ALG"]
    fep = [c[k] * w[k] for k in comps]
    fp = [FPA["subtotals"].get(k, 0) for k in comps]
    xs = range(len(comps))
    fig, ax = plt.subplots(figsize=(7.5, 3.6))
    ax.bar([x - 0.2 for x in xs], fp, 0.4, color="#9ecae1", label="Функціональні точки (UFP)")
    ax.bar([x + 0.2 for x in xs], fep, 0.4, color="#4c78a8", label="Feature points (UFeP)")
    for x, a, b in zip(xs, fp, fep):
        ax.text(x - 0.2, a + 8, str(a), ha="center", fontsize=8)
        ax.text(x + 0.2, b + 8, str(b), ha="center", fontsize=8)
    ax.set_xticks(list(xs), ["EI", "EO", "EQ", "ILF", "EIF", "Алгоритми"])
    ax.set_ylabel("Нескориговані точки")
    ax.set_ylim(0, 720)
    ax.grid(axis="x", visible=False)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=2, frameon=False)
    fig.tight_layout()
    fig.savefig(OUT / "01_feature_vs_fp.png")
    plt.close(fig)


def efforts() -> None:
    e = P["economy"]
    rows = [
        ("COCOMO за LOC (ПР2)", e["cocomo_loc"]["effort_pm"], "#bab0ac"),
        ("Функціональні точки (ПР3)", e["fp3"]["effort_pm"], "#9ecae1"),
        ("Feature points", e["fep"]["effort_pm"], "#4c78a8"),
        ("UCP, метод 2", e["ucp2"]["effort_pm"], "#54a24b"),
        ("UCP, метод 1, 36 год на точку", e["ucp36"]["effort_pm"], "#e45756"),
        ("UCP, метод 1, 20 год на точку", e["ucp20"]["effort_pm"], "#f58518"),
        ("Object points", e["op"]["effort_pm"], "#b279a2"),
    ]
    fig, ax = plt.subplots(figsize=(7.5, 3.8))
    ys = range(len(rows))
    ax.barh(list(ys), [r[1] for r in rows], color=[r[2] for r in rows])
    for y, r in zip(ys, rows):
        ax.text(r[1] + 5, y, f"{r[1]:.0f}", va="center", fontsize=9)
    ax.set_yticks(list(ys), [r[0] for r in rows])
    ax.invert_yaxis()
    ax.set_xlabel("Трудомісткість, людино-місяців")
    ax.set_xlim(0, 420)
    ax.grid(axis="y", visible=False)
    fig.tight_layout()
    fig.savefig(OUT / "02_efforts.png")
    plt.close(fig)


if __name__ == "__main__":
    compare_components()
    efforts()
    print("ok")
