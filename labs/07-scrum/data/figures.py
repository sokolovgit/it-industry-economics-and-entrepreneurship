"""Рисунки ПР7: оцінки історій двома командами, план релізу за спринтами."""

import json
from pathlib import Path

import matplotlib.pyplot as plt

HERE = Path(__file__).parent
OUT = HERE.parent / "docs" / "report" / "assets"
D = json.loads((HERE / "scrum.json").read_text(encoding="utf-8"))
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True, "grid.alpha": 0.3, "figure.dpi": 300})


def estimates() -> None:
    st = D["stories"]
    a = [r["sp"] for r in D["teams"]["A"]["stories"]]
    b = [r["sp"] for r in D["teams"]["B"]["stories"]]
    ref = [s["ref_days"] for s in st]
    xs = range(len(st))
    fig, ax = plt.subplots(figsize=(8, 3.6))
    ax.bar([x - 0.2 for x in xs], a, 0.4, color="#4c78a8", label="Команда A")
    ax.bar([x + 0.2 for x in xs], b, 0.4, color="#9ecae1", label="Команда B")
    ax.plot(list(xs), ref, "o", color="#e45756", ms=3.5, label="Довідкова складність за FP, ідеальні дні")
    ax.set_xticks(list(xs), [s["id"][2:] for s in st], fontsize=7)
    ax.set_xlabel("Користувацька історія, US№")
    ax.set_ylabel("Story points")
    ax.legend(frameon=False, fontsize=8)
    ax.grid(axis="x", visible=False)
    fig.tight_layout()
    fig.savefig(OUT / "01_estimates.png")
    plt.close(fig)


def plan() -> None:
    sp = {r["id"]: r["sp"] for r in D["teams"]["A"]["stories"]}
    n = max(p["sprint"] for p in D["plan"])
    per = [sum(p["sp"] for p in D["plan"] if p["sprint"] == s) for s in range(1, n + 1)]
    cum, c = [], 0
    for v in per:
        c += v
        cum.append(c)
    fig, ax = plt.subplots(figsize=(7.5, 3.4))
    ax.bar(range(1, n + 1), per, color="#9ecae1", label="Заплановано в спринті")
    ax.axhline(D["eco"]["velocity"], color="#e45756", ls="--", lw=1, label=f"Швидкість {D['eco']['velocity']:.0f} SP")
    for i, v in enumerate(per, 1):
        ax.text(i, v + 0.6, str(v), ha="center", fontsize=8)
    ax2 = ax.twinx()
    ax2.plot(range(1, n + 1), cum, "o-", color="#4c78a8", label="Накопичений обсяг")
    ax2.set_ylabel("Накопичені SP")
    ax2.spines["right"].set_visible(True)
    ax2.grid(False)
    ax.set_xlabel("Спринт")
    ax.set_ylabel("SP у спринті")
    ax.set_ylim(0, 45)
    h1, l1 = ax.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax.legend(h1 + h2, l1 + l2, frameon=False, fontsize=8, loc="upper left", ncol=1)
    fig.tight_layout()
    fig.savefig(OUT / "02_plan.png")
    plt.close(fig)


if __name__ == "__main__":
    estimates()
    plan()
    print("ok")
