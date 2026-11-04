"""Product Backlog Shopizer, оцінка Planning Poker двома командами (модель), економіка backlog.

Запуск: python3 data/scrum.py   (після ПР3)
Результат: data/scrum.json
"""

import csv
import json
import math
import random
import re
import statistics
from pathlib import Path

HERE = Path(__file__).parent
FP3 = HERE.parent.parent / "03-function-points" / "data"
TRANS = list(csv.DictReader(open(FP3 / "transactions.csv", encoding="utf-8")))
FPA = json.loads((FP3 / "fpa.json").read_text(encoding="utf-8"))
ECO2 = json.loads((HERE.parent.parent / "02-loc-metrics" / "data" / "economy.json").read_text(encoding="utf-8"))
SALARY, RATE = ECO2["salary_usd"], ECO2["usd_uah"]
VAF = FPA["vaf"]

CARDS = [0, 1, 2, 3, 5, 8, 13, 21, 34, 55]
DAYS_PER_UFP = 0.7  # ідеальних днів на одну нескориговану функціональну точку (розробка і тестування)
FOCUS = 0.7  # частка ідеального дня, яку команда фактично витрачає на роботу над історіями
SPRINT_DAYS, MONTH_DAYS = 10, 21.67
TEAM = ["Backend-розробник 1", "Backend-розробник 2", "Backend-розробник 3", "QA-інженер", "DevOps-інженер"]
FP_PER_PM = 10.4
SHIRT = [1, 3, 5, 8, 13]

# id, пріоритет (MoSCoW), назва, історія, операції (контролер, метод HTTP, нормований шлях)
S = [
    ("US01", "Must", "Реєстрація клієнта", "Як покупець, я хочу зареєструватись, щоб оформлювати замовлення", [("AuthenticateCustomerApi", "POST", "/customer/register")]),
    ("US02", "Must", "Вхід клієнта", "Як покупець, я хочу увійти в обліковий запис і продовжити сесію", [("AuthenticateCustomerApi", "POST", "/customer/login"), ("AuthenticateCustomerApi", "GET", "/customer/refresh")]),
    ("US03", "Should", "Відновлення і зміна пароля", "Як покупець, я хочу відновити або змінити пароль", [("AuthenticateCustomerApi", "POST", "/customer/password"), ("ResetCustomerPasswordApi", "POST", "/customer/password/reset/request"), ("ResetCustomerPasswordApi", "GET", "/customer/{}/reset/{}"), ("ResetCustomerPasswordApi", "POST", "/customer/{}/password/{}")]),
    ("US04", "Should", "Профіль і адреса клієнта", "Як покупець, я хочу переглядати і змінювати профіль та адресу", [("CustomerApi", "GET", "/customer/profile"), ("CustomerApi", "PATCH", "/customer/"), ("CustomerApi", "PATCH", "/customer/address")]),
    ("US05", "Must", "Перегляд категорій", "Як покупець, я хочу бачити дерево категорій", [("CategoryApi", "GET", "/category"), ("CategoryApi", "GET", "/category/{}")]),
    ("US06", "Must", "Список товарів", "Як покупець, я хочу переглядати список товарів з фільтрами", [("ProductApi", "GET", "/products"), ("CategoryApi", "GET", "/category/product/{}")]),
    ("US07", "Must", "Картка товару", "Як покупець, я хочу бачити картку товару з відгуками", [("ProductApi", "GET", "/product/{}"), ("ProductReviewApi", "GET", "/product/{}/reviews")]),
    ("US08", "Should", "Пошук товарів", "Як покупець, я хочу шукати товари з підказками", [("SearchApi", "POST", "/search"), ("SearchApi", "POST", "/search/autocomplete")]),
    ("US09", "Could", "Відгуки про товари", "Як покупець, я хочу залишати, змінювати і видаляти відгуки", [("ProductReviewApi", "POST", "/products/{}/reviews"), ("ProductReviewApi", "PUT", "/products/{}/reviews/{}"), ("ProductReviewApi", "DELETE", "/products/{}/reviews/{}")]),
    ("US10", "Must", "Додавання товару в кошик", "Як покупець, я хочу додати товар у кошик", [("ShoppingCartApi", "POST", "/cart")]),
    ("US11", "Must", "Зміна кошика", "Як покупець, я хочу змінювати кількість і видаляти товари з кошика", [("ShoppingCartApi", "PUT", "/cart/{}"), ("ShoppingCartApi", "DELETE", "/cart/{}/product/{}"), ("ShoppingCartApi", "POST", "/cart/{}/multi")]),
    ("US12", "Must", "Перегляд кошика", "Як покупець, я хочу бачити кошик із сумами", [("ShoppingCartApi", "GET", "/cart/{}"), ("ShoppingCartApi", "GET", "/customer/cart")]),
    ("US13", "Could", "Промокод", "Як покупець, я хочу застосувати промокод до кошика", [("ShoppingCartApi", "POST", "/cart/{}/promo/{}")]),
    ("US14", "Must", "Підсумок замовлення", "Як покупець, я хочу бачити підсумок із податками і знижками", [("OrderTotalApi", "GET", "/cart/{}/total")]),
    ("US15", "Must", "Вартість доставки", "Як покупець, я хочу бачити варіанти і вартість доставки", [("OrderShippingApi", "GET", "/cart/{}/shipping"), ("OrderShippingApi", "POST", "/cart/{}/shipping")]),
    ("US16", "Must", "Оформлення замовлення", "Як покупець, я хочу оформити замовлення з кошика", [("OrderApi", "POST", "/cart/{}/checkout")]),
    ("US17", "Must", "Оплата замовлення", "Як покупець, я хочу оплатити замовлення", [("OrderPaymentApi", "POST", "/cart/{}/payment/init")]),
    ("US18", "Should", "Історія замовлень", "Як покупець, я хочу переглядати свої замовлення", [("OrderApi", "GET", "/orders"), ("OrderApi", "GET", "/orders/{}")]),
    ("US19", "Must", "Створення товару", "Як адміністратор, я хочу створити товар", [("ProductApi", "POST", "/product")]),
    ("US20", "Must", "Редагування і видалення товару", "Як адміністратор, я хочу змінювати і видаляти товари", [("ProductApi", "PUT", "/product/{}"), ("ProductApi", "PATCH", "/product/{}"), ("ProductApi", "DELETE", "/product/{}")]),
    ("US21", "Should", "Зображення товару", "Як адміністратор, я хочу завантажувати і видаляти зображення", [("ProductImageApi", "POST", "/product/{}/image"), ("ProductImageApi", "GET", "/product/{}/images"), ("ProductImageApi", "DELETE", "/product/{}/image/{}")]),
    ("US22", "Must", "Керування категоріями", "Як адміністратор, я хочу керувати категоріями", [("CategoryApi", "POST", "/category"), ("CategoryApi", "PUT", "/category/{}"), ("CategoryApi", "PATCH", "/category/{}/visible"), ("CategoryApi", "PUT", "/category/{}/move/{}"), ("CategoryApi", "DELETE", "/category/{}")]),
    ("US23", "Must", "Статус замовлення", "Як адміністратор, я хочу змінювати статус і клієнта замовлення", [("OrderApi", "PUT", "/orders/{}/status"), ("OrderApi", "PATCH", "/orders/{}/customer")]),
    ("US24", "Should", "Керування платежами", "Як адміністратор, я хочу авторизувати, списати і повернути платіж", [("OrderPaymentApi", "POST", "/orders/{}/authorize"), ("OrderPaymentApi", "POST", "/orders/{}/capture"), ("OrderPaymentApi", "POST", "/orders/{}/refund"), ("OrderPaymentApi", "GET", "/orders/payment/capturable")]),
    ("US25", "Must", "Налаштування магазину", "Як адміністратор, я хочу створити і налаштувати магазин", [("MerchantStoreApi", "POST", "/store"), ("MerchantStoreApi", "PUT", "/store/{}"), ("MerchantStoreApi", "DELETE", "/store/{}"), ("MerchantStoreApi", "POST", "/store/{}/marketing"), ("MerchantStoreApi", "POST", "/store/{}/marketing/logo")]),
    ("US26", "Could", "Перевірка унікальності", "Як адміністратор, я хочу перевіряти унікальність коду товару, категорії і магазину", [("ProductApi", "GET", "/product/unique"), ("CategoryApi", "GET", "/category/unique"), ("MerchantStoreApi", "GET", "/store/unique")]),
    ("US27", "Should", "Керування клієнтами", "Як адміністратор, я хочу переглядати список і дані клієнтів", [("CustomerApi", "GET", "/customers"), ("CustomerApi", "GET", "/customer/{}")]),
]


def normalize(path):
    p = re.sub(r"^/(api|services)/(v\d+/)?", "/", path)
    p = re.sub(r"/(private|auth|public)(?=/|$)", "", p)
    return re.sub(r"\{[^}]*\}", "{}", p)


OPS = {}
for r in TRANS:
    k = (r["controller"], r["http"], normalize(r["path"]))
    if k not in OPS or int(r["ufp"]) > int(OPS[k]["ufp"]):
        OPS[k] = r


def nearest_card(x):
    return min(CARDS[1:], key=lambda c: abs(math.log(c) - math.log(max(x, 0.5))))


def poker(rng, base_days, biases, sigma=0.25):
    """Planning Poker: перший раунд за власними оцінками, далі обговорення і зближення голосів."""
    votes = [nearest_card(base_days * b * math.exp(rng.gauss(0, sigma))) for b in biases]
    rounds = 1
    while rounds < 4:
        idx = sorted(CARDS.index(v) for v in votes)
        if idx[-1] - idx[0] <= 1:
            break
        med = statistics.median(math.log(v) for v in votes)
        votes = [nearest_card(math.exp(0.35 * math.log(v) + 0.65 * med + rng.gauss(0, 0.08))) for v in votes]
        rounds += 1
    final = sorted(votes)[len(votes) // 2]  # медіана голосів в останньому раунді
    return final, rounds, votes


def spearman(a, b):
    def ranks(x):
        order = sorted(range(len(x)), key=lambda i: x[i])
        r = [0.0] * len(x)
        i = 0
        while i < len(x):
            j = i
            while j + 1 < len(x) and x[order[j + 1]] == x[order[i]]:
                j += 1
            for k in range(i, j + 1):
                r[order[k]] = (i + j) / 2 + 1
            i = j + 1
        return r
    ra, rb = ranks(a), ranks(b)
    ma, mb = statistics.mean(ra), statistics.mean(rb)
    num = sum((x - ma) * (y - mb) for x, y in zip(ra, rb))
    return num / math.sqrt(sum((x - ma) ** 2 for x in ra) * sum((y - mb) ** 2 for y in rb))


def main():
    stories = []
    for sid, prio, title, text, ops in S:
        rows = [OPS[k] for k in ops]  # KeyError, якщо операції немає в ПР3
        ufp = sum(int(r["ufp"]) for r in rows)
        stories.append({"id": sid, "priority": prio, "title": title, "text": text, "ops": len(ops), "ufp": ufp, "ref_days": DAYS_PER_UFP * ufp})
    teams = {}
    for name, seed in (("A", 7), ("B", 11)):
        rng = random.Random(seed)
        biases = [math.exp(rng.gauss(0, 0.12)) * (1.10 if "QA" in p else 1.0) for p in TEAM]
        res = []
        for s in stories:
            final, rounds, votes = poker(rng, s["ref_days"], biases)
            res.append({"id": s["id"], "sp": final, "rounds": rounds, "first": None, "votes": votes})
        teams[name] = {"biases": biases, "stories": res}
    # T-shirt: одне голосування без обговорення, розміри XS, S, M, L, XL = 1, 3, 5, 8, 13
    tshirt = {}
    for name, seed in (("A", 7), ("B", 11)):
        rng = random.Random(seed)
        biases = teams[name]["biases"]
        vals = []
        for st in stories:
            votes = [min(SHIRT, key=lambda c: abs(math.log(c) - math.log(max(st["ref_days"] * b * math.exp(rng.gauss(0, 0.25)), 0.5)))) for b in biases]
            vals.append(sorted(votes)[len(votes) // 2])
        tshirt[name] = vals
    sa = [r["sp"] for r in teams["A"]["stories"]]
    sb = [r["sp"] for r in teams["B"]["stories"]]
    ufp = [s["ufp"] for s in stories]
    ref = [nearest_card(s["ref_days"]) for s in stories]
    agree = {
        "exact": sum(1 for x, y in zip(sa, sb) if x == y) / len(sa),
        "within1": sum(1 for x, y in zip(sa, sb) if abs(CARDS.index(x) - CARDS.index(y)) <= 1) / len(sa),
        "spearman_ab": spearman(sa, sb),
        "spearman_a_ufp": spearman(sa, ufp),
        "spearman_b_ufp": spearman(sb, ufp),
        "rounds_a": statistics.mean(r["rounds"] for r in teams["A"]["stories"]),
        "rounds_b": statistics.mean(r["rounds"] for r in teams["B"]["stories"]),
        "exact_ref_a": sum(1 for x, y in zip(sa, ref) if x == y) / len(sa),
        "exact_ref_b": sum(1 for x, y in zip(sb, ref) if x == y) / len(sb),
    }
    def mre(sp):
        return statistics.mean(abs(x - st["ref_days"]) / st["ref_days"] for x, st in zip(sp, stories))

    methods = {
        "Planning Poker, команда A": {"sp": sa, "rounds": agree["rounds_a"]},
        "Planning Poker, команда B": {"sp": sb, "rounds": agree["rounds_b"]},
        "T-shirt, команда A": {"sp": tshirt["A"], "rounds": 1.0},
        "T-shirt, команда B": {"sp": tshirt["B"], "rounds": 1.0},
    }
    for m in methods.values():
        m["total"] = sum(m["sp"])
        m["mre"] = mre(m["sp"])
        m["spearman_ufp"] = spearman(m["sp"], ufp)
    methods["T-shirt, команди A і B"] = {"exact": sum(1 for x, y in zip(tshirt["A"], tshirt["B"]) if x == y) / len(sa)}
    methods["Planning Poker, команди A і B"] = {"exact": agree["exact"]}
    # економіка
    velocity = len(TEAM) * SPRINT_DAYS * FOCUS
    sprint_cost = (len(TEAM) + 1.0) * SALARY * SPRINT_DAYS / MONTH_DAYS  # команда з 5 осіб, Scrum Master і Product Owner по 0.5
    eco = {"velocity": velocity, "sprint_cost_usd": sprint_cost}
    for name, sp in (("A", sa), ("B", sb)):
        total = sum(sp)
        sprints = math.ceil(total / velocity)
        eco[name] = {"sp": total, "sprints": sprints, "weeks": sprints * 2, "cost_usd": sprints * sprint_cost, "cost_uah": sprints * sprint_cost * RATE,
                     "usd_per_sp": sprints * sprint_cost / total, "pm": sprints * (len(TEAM) + 1.0) * SPRINT_DAYS / MONTH_DAYS}
    ufp_total = sum(ufp)
    afp = ufp_total * VAF
    eco["fp"] = {"ufp": ufp_total, "afp": afp, "pm": afp / FP_PER_PM, "cost_usd": afp / FP_PER_PM * SALARY, "usd_per_afp": SALARY / FP_PER_PM, "total_afp_share": afp / FPA["afp"]}
    eco["ref_days_total"] = sum(s["ref_days"] for s in stories)
    # план релізу: історії за пріоритетом розміщуються в першому спринті з достатньою ємністю
    order = {"Must": 0, "Should": 1, "Could": 2}
    sp_a = {r["id"]: r["sp"] for r in teams["A"]["stories"]}
    plan, free = [], []  # free[i] – вільна ємність спринту i + 1
    for st in sorted(stories, key=lambda s: (order[s["priority"]], s["id"])):
        v = sp_a[st["id"]]
        k = next((i for i, f in enumerate(free) if f >= v), None)
        if k is None:
            free.append(velocity)
            k = len(free) - 1
        free[k] -= v
        plan.append({"id": st["id"], "sprint": k + 1, "sp": v})
    out = {"methods": methods, "stories": stories, "teams": teams, "agree": agree, "eco": eco, "plan": plan, "team": TEAM, "cards": CARDS,
           "constants": {"days_per_ufp": DAYS_PER_UFP, "focus": FOCUS, "sprint_days": SPRINT_DAYS, "month_days": MONTH_DAYS}}
    (HERE / "scrum.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("історій", len(stories), "UFP", ufp_total, "AFP", round(afp, 1), "ідеальних днів", round(eco["ref_days_total"], 1))
    print("SP A", sum(sa), "SP B", sum(sb), "довідково", sum(ref))
    print({k: round(v, 3) for k, v in agree.items()})
    for k, v in methods.items():
        print(k, {a: (round(b, 3) if isinstance(b, float) else b) for a, b in v.items() if a != "sp"})
    print({k: v for k, v in eco.items() if k in ("velocity", "sprint_cost_usd")})
    for n in "AB":
        print(n, {k: round(v, 1) for k, v in eco[n].items()})
    print("FP", {k: round(v, 2) for k, v in eco["fp"].items()})
    print("плану спринтів", max(p["sprint"] for p in plan))
    for s, a, b in zip(stories, sa, sb):
        print(s["id"], s["priority"], s["ufp"], round(s["ref_days"], 1), a, b)


if __name__ == "__main__":
    main()
