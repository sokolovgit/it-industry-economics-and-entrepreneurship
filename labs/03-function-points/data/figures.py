"""Рисунки ПР3: структура нескоригованих точок і порівняння оцінок трудомісткості."""

import json
from pathlib import Path

import matplotlib.pyplot as plt

HERE = Path(__file__).parent
OUT = HERE.parent / "docs" / "report" / "assets"
FP = json.loads((HERE / "fpa.json").read_text(encoding="utf-8"))
W = {"ILF": (7, 10, 15), "EIF": (5, 7, 10), "EI": (3, 4, 6), "EO": (4, 5, 7), "EQ": (3, 4, 6)}

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True, "grid.alpha": 0.3, "figure.dpi": 300})


def structure() -> None:
    comps = ["ILF", "EIF", "EI", "EO", "EQ"]
    colors = {"L": "#9ecae1", "A": "#4c78a8", "H": "#1f3b63"}
    names = {"L": "Низький", "A": "Середній", "H": "Високий"}
    fig, ax = plt.subplots(figsize=(7.5, 3.6))
    left = [0] * len(comps)
    for i, lv in enumerate("LAH"):
        vals = [FP["counts"][c][lv] * W[c][i] for c in comps]
        ax.barh(comps, vals, left=left, color=colors[lv], label=names[lv])
        left = [a + b for a, b in zip(left, vals)]
    for i, c in enumerate(comps):
        ax.text(left[i] + 8, i, str(FP["subtotals"][c]), va="center", fontsize=9)
    ax.invert_yaxis()
    ax.set_xlabel("Нескориговані функціональні точки")
    ax.set_xlim(0, 660)
    ax.grid(axis="y", visible=False)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.22), ncol=3, frameon=False)
    fig.tight_layout()
    fig.savefig(OUT / "01_structure.png")
    plt.close(fig)


def estimates() -> None:
    e = FP["economy"]
    labels = ["Продуктивність\n(10.4 FP на місяць)", "COCOMO за AFP\n(116 KLOC)", "COCOMO за LOC\n(72 KLOC, ПР2)"]
    vals = [e["productivity"]["effort"], e["cocomo_from_fp"]["effort"], e["cocomo_measured"]["effort"]]
    fig, ax = plt.subplots(figsize=(7.5, 3.4))
    bars = ax.bar(labels, vals, color=["#54a24b", "#4c78a8", "#bab0ac"], width=0.55)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 10, f"{v:.0f}", ha="center", fontsize=10)
    ax.set_ylabel("Трудомісткість, людино-місяців")
    ax.set_ylim(0, 720)
    ax.grid(axis="x", visible=False)
    fig.tight_layout()
    fig.savefig(OUT / "02_estimates.png")
    plt.close(fig)


if __name__ == "__main__":
    structure()
    estimates()
    print("ok")
