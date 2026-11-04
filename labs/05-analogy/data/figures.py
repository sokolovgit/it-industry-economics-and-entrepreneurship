"""Рисунки ПР5: відстані до нового проєкту, калібрування методу."""

import json
from pathlib import Path

import matplotlib.pyplot as plt

HERE = Path(__file__).parent
OUT = HERE.parent / "docs" / "report" / "assets"
A = json.loads((HERE / "analogy.json").read_text(encoding="utf-8"))
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True, "grid.alpha": 0.3, "figure.dpi": 300})


def distances() -> None:
    rows = sorted(A["distances"], key=lambda d: d["euclid"])
    near = {d["repo"] for d in rows[:3]}
    fig, ax = plt.subplots(figsize=(7.5, 5.2))
    ys = range(len(rows))
    ax.barh(list(ys), [d["euclid"] for d in rows], color=["#e45756" if d["repo"] in near else "#9ecae1" for d in rows])
    for y, d in zip(ys, rows):
        ax.text(d["euclid"] + 0.01, y, f"{d['euclid']:.2f}", va="center", fontsize=8)
    ax.set_yticks(list(ys), [d["repo"].split("/")[1] for d in rows])
    ax.invert_yaxis()
    ax.set_xlabel("Евклідова відстань до Shopizer (нормовані атрибути)")
    ax.set_xlim(0, 1.7)
    ax.grid(axis="y", visible=False)
    fig.tight_layout()
    fig.savefig(OUT / "01_distances.png")
    plt.close(fig)


def calibration() -> None:
    cfg = A["configs"]
    fig, axes = plt.subplots(1, 2, figsize=(8, 3.4), sharey=True)
    for ax, adj, title in zip(axes, (False, True), ("Без корекції за розміром", "З корекцією за розміром")):
        for metric, color, name in (("euclid", "#4c78a8", "Евклід"), ("manhattan", "#f58518", "Манхеттен")):
            for stat, ls in (("mean", "-"), ("median", "--")):
                pts = sorted((c["k"], c["mmre"] * 100) for c in cfg if c["metric"] == metric and c["stat"] == stat and c["size_adj"] == adj)
                ax.plot([p[0] for p in pts], [p[1] for p in pts], ls, marker="o", color=color, label=f"{name}, {'середнє' if stat == 'mean' else 'медіана'}")
        ax.set_title(title, fontsize=10)
        ax.set_xlabel("Кількість аналогів k")
        ax.set_xticks([1, 2, 3, 4, 5])
    axes[0].set_ylabel("MMRE, %")
    axes[1].legend(frameon=False, fontsize=7.5)
    fig.tight_layout()
    fig.savefig(OUT / "02_calibration.png")
    plt.close(fig)


if __name__ == "__main__":
    distances()
    calibration()
    print("ok")
