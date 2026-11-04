"""Оцінка трудомісткості Shopizer за методом аналогій.

Запуск: python3 data/analogy.py   (після collect.py і shopizer.py)
Результат: data/analogy.json, data/database.csv
"""

import csv
import itertools
import json
import math
import statistics
from pathlib import Path

HERE = Path(__file__).parent
RAW = [r for r in json.loads((HERE / "projects_raw.json").read_text(encoding="utf-8")) if "error" not in r]
NEW = json.loads((HERE / "shopizer.json").read_text(encoding="utf-8"))
ATTRS = [("modules", "Збірних модулів"), ("deps", "Залежностей"), ("test_share", "Частка тестів, %"), ("comment_ratio", "Частка коментарів, %"), ("beans", "Spring-компонентів"), ("endpoints", "Ендпоінтів")]
SALARY, RATE = 2500, 45.666


def prepare(r):
    r = dict(r)
    r["kloc"] = r["code"] / 1000
    r["test_share"] = 100 * r["test"] / r["code"] if r["code"] else 0
    r["comment_ratio"] = 100 * r["comment"] / r["code"] if r["code"] else 0
    r["effort"] = r["contributor_months"]
    return r


def select(rows, n=20):
    ok = [prepare(r) for r in rows if 1800 <= r["code"] <= 300000 and r["commits"] >= 20 and r["contributor_months"] >= 5 and (r["endpoints"] + r["beans"] > 0 or r["modules"] > 0)]
    ok.sort(key=lambda r: r["repo"].lower())
    return ok[:n] if len(ok) <= n else pick(ok, n)


def pick(ok, n):
    """Якщо кандидатів більше n, береться n найближчих за розміром до Shopizer (у межах 0.2–5 розміру)."""
    ok = sorted(ok, key=lambda r: abs(math.log(r["code"] / NEW["code"])))[:n]
    return sorted(ok, key=lambda r: r["repo"].lower())


def normalize(rows, new):
    allp = rows + [new]
    lo = {a: min(p[a] for p in allp) for a, _ in ATTRS}
    hi = {a: max(p[a] for p in allp) for a, _ in ATTRS}
    return lambda p: [(p[a] - lo[a]) / (hi[a] - lo[a]) if hi[a] > lo[a] else 0 for a, _ in ATTRS]


def dist(u, v, metric):
    if metric == "euclid":
        return math.sqrt(sum((x - y) ** 2 for x, y in zip(u, v)))
    return sum(abs(x - y) for x, y in zip(u, v))


def estimate(target, pool, norm, metric, k, stat, size_adj):
    tv = norm(target)
    near = sorted(pool, key=lambda p: dist(tv, norm(p), metric))[:k]
    vals = [p["effort"] * (target["kloc"] / p["kloc"] if size_adj else 1) for p in near]
    return (statistics.mean(vals) if stat == "mean" else statistics.median(vals)), near


def main():
    analogs = select(RAW)
    new = prepare({**NEW, "contributor_months": 0})
    norm = normalize(analogs, new)
    out = {"n": len(analogs), "analogs": analogs, "new": new}

    # матриця відстаней до нового проєкту
    tv = norm(new)
    rows = []
    for p in analogs:
        v = norm(p)
        rows.append({"repo": p["repo"], "euclid": dist(tv, v, "euclid"), "manhattan": dist(tv, v, "manhattan")})
    out["distances"] = rows

    # калібрування: leave-one-out по всіх конфігураціях
    configs = []
    for metric, k, stat, adj in itertools.product(("euclid", "manhattan"), (1, 2, 3, 4, 5), ("mean", "median"), (False, True)):
        mre = []
        for i, t in enumerate(analogs):
            pool = analogs[:i] + analogs[i + 1:]
            est, _ = estimate(t, pool, norm, metric, k, stat, adj)
            mre.append(abs(est - t["effort"]) / t["effort"])
        configs.append({"metric": metric, "k": k, "stat": stat, "size_adj": adj, "mmre": statistics.mean(mre), "mdmre": statistics.median(mre), "pred25": sum(1 for x in mre if x <= 0.25) / len(mre), "pred50": sum(1 for x in mre if x <= 0.5) / len(mre)})
    out["configs"] = configs
    best = min(configs, key=lambda c: c["mmre"])
    out["best"] = best

    # оцінка для нового проєкту
    def run(metric, k, stat, adj):
        est, near = estimate(new, analogs, norm, metric, k, stat, adj)
        return {"estimate": est, "near": [p["repo"] for p in near], "cost_usd": est * SALARY, "cost_uah": est * SALARY * RATE}

    out["main"] = run("euclid", 3, "mean", False)
    out["main_adj"] = run("euclid", 3, "mean", True)
    out["main_manhattan"] = run("manhattan", 3, "mean", False)
    out["main_manhattan_adj"] = run("manhattan", 3, "mean", True)
    out["best_est"] = run(best["metric"], best["k"], best["stat"], best["size_adj"])
    # чутливість до складу бази: без проєктів зі слабкою історією комітів і без навчальних
    EDU = {"spring-projects/spring-petclinic", "spring-petclinic/spring-petclinic-microservices", "sqshq/piggymetrics"}
    variants = {
        "all": ("Уся база (20 проєктів)", analogs),
        "dense": ("Без проєктів із менше ніж 5 комітів на KLOC", [p for p in analogs if p["commits"] / p["kloc"] >= 5]),
        "noedu": ("Без навчальних проєктів (petclinic, petclinic-microservices, piggymetrics)", [p for p in analogs if p["repo"] not in EDU]),
        "both": ("Без обох груп", [p for p in analogs if p["commits"] / p["kloc"] >= 5 and p["repo"] not in EDU]),
    }
    sens = []
    for key, (title, sub) in variants.items():
        nrm = normalize(sub, new)
        row = {"key": key, "title": title, "n": len(sub)}
        for tag, (metric, k, adj) in {"euclid": ("euclid", 3, False), "euclid_adj": ("euclid", 3, True), "manhattan_adj": ("manhattan", 2, True)}.items():
            est, near = estimate(new, sub, nrm, metric, k, "mean", adj)
            row[tag] = est
            row[tag + "_near"] = [q["repo"] for q in near]
        mre = []
        for i, t in enumerate(sub):
            est, _ = estimate(t, sub[:i] + sub[i + 1:], nrm, "manhattan", 2, "mean", True)
            mre.append(abs(est - t["effort"]) / t["effort"])
        row["loo_mmre"] = statistics.mean(mre)
        row["loo_pred25"] = sum(1 for x in mre if x <= 0.25) / len(mre)
        sens.append(row)
    out["sensitivity"] = sens
    # продуктивність аналогів
    out["productivity"] = {"median_pm_per_kloc": statistics.median(p["effort"] / p["kloc"] for p in analogs)}
    (HERE / "analogy.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    with open(HERE / "database.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["repo", "commit"] + [a for a, _ in ATTRS] + ["language", "code", "effort"])
        for p in analogs + [new]:
            w.writerow([p["repo"], p.get("commit", ""), *[round(p[a], 2) for a, _ in ATTRS], "Java", p["code"], p["effort"] if p is not new else ""])
    print("аналогів", len(analogs), "кращий конфіг", {k: (round(v, 3) if isinstance(v, float) else v) for k, v in best.items()})
    for key in ("main", "main_adj", "main_manhattan", "main_manhattan_adj", "best_est"):
        r = out[key]
        print(key, round(r["estimate"], 1), r["near"])
    for r in sens:
        print("чутливість", r["key"], r["n"], round(r["euclid"], 1), round(r["euclid_adj"], 1), round(r["manhattan_adj"], 1), "LOO MMRE", round(r["loo_mmre"] * 100), "Pred25", r["loo_pred25"])
    print("медіанна продуктивність, людино-місяців на KLOC:", round(out["productivity"]["median_pm_per_kloc"], 2))


if __name__ == "__main__":
    main()
