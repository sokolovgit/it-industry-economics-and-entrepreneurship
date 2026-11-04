"""Feature points, Object points, Use-case points (два методи) для Shopizer.

Запуск: python3 data/points.py   (після ПР2 і ПР3: використовує їх результати)
Результат: data/points.json
"""

import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).parent
FP3 = HERE.parent.parent / "03-function-points" / "data"
PR2 = HERE.parent.parent / "02-loc-metrics" / "data"
TRANS = list(csv.DictReader(open(FP3 / "transactions.csv", encoding="utf-8")))
FPA = json.loads((FP3 / "fpa.json").read_text(encoding="utf-8"))
ILF = json.loads((FP3 / "ilf.json").read_text(encoding="utf-8"))
ECO2 = json.loads((PR2 / "economy.json").read_text(encoding="utf-8"))

SALARY, RATE = ECO2["salary_usd"], ECO2["usd_uah"]
HOURS_PM = 160  # годин у людино-місяці

# ---------- Feature points (Jones, 1986) ----------
FEP_W = {"EI": 4, "EO": 5, "EQ": 4, "ILF": 7, "EIF": 7, "ALG": 3}
ALGORITHMS = [
    ("Остаточна ціна товару (знижки, атрибути, клієнт)", "PricingServiceImpl.calculateProductPrice"),
    ("Підсумок кошика", "ShoppingCartCalculationServiceImpl.calculate"),
    ("Підсумок замовлення", "OrderServiceImpl.calculateShoppingCartTotal"),
    ("Розрахунок податків", "TaxServiceImpl.calculateTax"),
    ("Вартість доставки за вагою", "CustomWeightBasedShippingQuote"),
    ("Вартість доставки за відстанню", "PriceByDistanceShippingQuoteRules"),
    ("Вартість доставки за правилами", "CustomShippingQuoteRules, ShippingDecisionPreProcessorImpl"),
    ("Пакування товарів у коробки", "DefaultPackagingImpl"),
    ("Запит і розбір відповіді UPS", "UPSShippingQuote"),
    ("Запит і розбір відповіді USPS", "USPSShippingQuote"),
    ("Знижка за промокодом", "PromoCodeCalculatorModule"),
    ("Правила коду доставки виробника", "ManufacturerShippingCodeOrderTotalModuleImpl"),
    ("Шифрування і дешифрування даних", "EncryptionImpl"),
    ("Генерація і перевірка токена JWT", "JWTTokenUtil"),
    ("Перевірка і генерація пароля", "CredentialsServiceImpl"),
    ("Перевірка номера кредитної картки", "PaymentServiceImpl.validateCreditCardNumber"),
    ("Масштабування зображень", "ProductImageSizeUtils"),
    ("Середній рейтинг відгуків", "ProductReviewServiceImpl, CustomerReviewServiceImpl"),
    ("Індексація і повнотекстовий пошук", "SearchServiceImpl"),
]

# ---------- Object points (COCOMO II, application composition) ----------
SCREEN_MATRIX = {  # (рядок за кількістю представлень, стовпець за кількістю таблиць) -> складність
    (0, 0): "s", (0, 1): "s", (0, 2): "m",
    (1, 0): "s", (1, 1): "m", (1, 2): "d",
    (2, 0): "m", (2, 1): "d", (2, 2): "d",
}
SCREEN_W = {"s": 1, "m": 2, "d": 3}
REPORT_W = {"s": 2, "m": 5, "d": 8}
GL3_W = 10
EMAIL_TEMPLATES = 20
GL3 = [
    ("Модулі оплати (BeanStream, Braintree, MoneyOrder, PayPal Express, PayPal REST, Stripe, Stripe3)", 7),
    ("Модулі доставки (UPS, USPS, за вагою, за відстанню, за правилами, самовивіз)", 6),
    ("Відправлення пошти (SMTP, AWS SES)", 2),
    ("Сховища файлів (локальне, AWS S3, GCP, Infinispan)", 4),
    ("Модулі підсумку замовлення (промокод, код доставки виробника)", 2),
    ("Формування рахунку-фактури (ODS)", 1),
    ("Шифрування", 1),
]
PROD = {"дуже низька": 4, "низька": 7, "номінальна": 13, "висока": 25, "дуже висока": 50}

# ---------- Use-case points (Karner) ----------
ACTORS = [
    ("Покупець (роль CUSTOMER)", 3, "особа через вітрину, графічний інтерфейс"),
    ("Адміністратор магазину (ADMIN, ADMIN_STORE, ADMIN_CATALOGUE, ADMIN_ORDER)", 3, "особа через адміністративний інтерфейс"),
    ("Адміністратор роздрібного продавця (ADMIN_RETAILER)", 3, "особа через адміністративний інтерфейс"),
    ("Суперадміністратор (SUPERADMIN)", 3, "особа через адміністративний інтерфейс"),
    ("Платіжний шлюз", 1, "інша система, визначений API"),
    ("Служба доставки UPS", 1, "інша система, визначений API"),
    ("Служба доставки USPS", 1, "інша система, визначений API"),
    ("Поштовий сервер", 2, "інша система, протокол SMTP"),
    ("Хмарне сховище файлів", 1, "інша система, визначений API"),
]
TECH = [  # (характеристика, вага, оцінка, обґрунтування)
    ("T1 Розподілена система", 2, 3, "серверна частина відокремлена від вітрини, адмінки, кешу і сховищ"),
    ("T2 Час відгуку", 2, 2, "кешування є, жорстких вимог немає"),
    ("T3 Ефективність роботи користувача", 1, 3, "кілька мов і валют, повідомлення валідації"),
    ("T4 Складна внутрішня обробка", 1, 4, "ціни, податки, доставка, пакування"),
    ("T5 Повторне використання коду", 1, 3, "модулі оплати і доставки замінні"),
    ("T6 Зручність встановлення", 0.5, 3, "Maven, Docker, схема бази створюється автоматично"),
    ("T7 Зручність використання", 0.5, 3, "документація Swagger для клієнтів API"),
    ("T8 Переносимість", 2, 4, "Java, кілька СУБД і сховищ"),
    ("T9 Зручність змін", 1, 3, "налаштовувані атрибути і модулі"),
    ("T10 Паралельність", 1, 3, "багатокористувацький веб-сервіс"),
    ("T11 Безпека", 1, 5, "JWT, ролі, шифрування даних"),
    ("T12 Доступ третіх сторін", 1, 5, "відкритий API для вітрин і інтеграцій"),
    ("T13 Спеціальне навчання користувачів", 1, 1, "навчання потрібне лише розробникам клієнтів API"),
]
ENV = [
    ("F1 Знайомство з процесом розробки", 1.5, 3, "склад команди невідомий, прийнято середній рівень"),
    ("F2 Досвід у предметній області", 0.5, 4, "електронна комерція, проєкт існує з 2012 року"),
    ("F3 Досвід в ООП", 1, 5, "Java"),
    ("F4 Здібності провідного аналітика", 0.5, 3, "прийнято середній рівень"),
    ("F5 Мотивація", 1, 3, "прийнято середній рівень"),
    ("F6 Стабільність вимог", 2, 3, "зрілий продукт, але є версії API v1 і v2"),
    ("F7 Частково зайняті працівники", -1, 3, "відкритий проєкт, прийнято середній рівень"),
    ("F8 Складна мова програмування", -1, 1, "Java"),
]
UC = {  # назва -> (контролери, актори)
    "Автентифікація і відновлення пароля клієнта": (["AuthenticateCustomerApi", "ResetCustomerPasswordApi"], "Покупець"),
    "Керування профілем клієнта": (["CustomerApi", "CustomerNewsletterApi"], "Покупець"),
    "Перегляд товарів і категорій": (["ProductApi", "ProductApiV2", "CategoryApi", "ProductPriceApi"], "Покупець; адміністратор магазину"),
    "Пошук товарів": (["SearchApi", "SearchToolsApi"], "Покупець"),
    "Відгуки про товари і клієнтів": (["ProductReviewApi", "CustomerReviewApi"], "Покупець; адміністратор магазину"),
    "Керування кошиком": (["ShoppingCartApi"], "Покупець"),
    "Розрахунок підсумку замовлення": (["OrderTotalApi"], "Покупець"),
    "Розрахунок вартості доставки": (["OrderShippingApi"], "Покупець; служби доставки"),
    "Оплата замовлення": (["OrderPaymentApi", "PaymentApi"], "Покупець; платіжний шлюз"),
    "Оформлення і перегляд замовлень": (["OrderApi", "OrderStatusHistoryApi"], "Покупець; адміністратор магазину; пошта"),
    "Керування каталогом і категоріями": (["CatalogApi"], "Адміністратор магазину"),
    "Керування варіантами товару": (["ProductVariantApi", "ProductVariantGroupApi", "ProductVariationApi"], "Адміністратор магазину"),
    "Керування опціями товару": (["ProductAttributeOptionApi", "ProductPropertySetApi"], "Адміністратор магазину"),
    "Керування зображеннями товару": (["ProductImageApi", "ImagesController"], "Адміністратор магазину; хмарне сховище"),
    "Керування типами, виробниками і групами": (["ProductTypeApi", "ProductManufacturerApi", "ProductGroupApi", "ProductRelationshipApi", "ProductInventoryApi"], "Адміністратор магазину"),
    "Керування контентом і файлами": (["ContentApi", "ContentAdministrationApi", "FilesController"], "Адміністратор магазину; хмарне сховище"),
    "Керування магазином": (["MerchantStoreApi", "MarketPlaceApi", "StoreContactRESTController", "ContactApi", "DefaultController"], "Адміністратор магазину; адміністратор роздрібного продавця; пошта"),
    "Керування користувачами і правами": (["UserApi", "AuthenticateUserApi", "ResetUserPasswordApi", "SecurityApi"], "Суперадміністратор; адміністратор магазину"),
    "Налаштування доставки": (["ShippingConfigurationApi", "ShippingExpeditionApi"], "Адміністратор магазину"),
    "Керування податками": (["TaxClassApi", "TaxRatesApi"], "Адміністратор магазину"),
    "Керування модулями, конфігурацією і кешем": (["ModulesApi", "ConfigurationsApi", "PublicConfigsApi", "CacheApi", "SystemRESTController", "OptinApi"], "Суперадміністратор; адміністратор магазину"),
    "Довідники": (["ReferencesApi"], "Покупець; адміністратор магазину"),
}


def normalize(path: str) -> str:
    p = re.sub(r"^/(api|services)/(v\d+/)?", "/", path)
    p = re.sub(r"/(private|auth|public)(?=/|$)", "", p)
    return re.sub(r"\{[^}]*\}", "{}", p)


def main() -> None:
    out: dict = {}
    c = FPA["counts"]
    n_ei, n_eo, n_eq = (sum(c[t].values()) for t in ("EI", "EO", "EQ"))
    n_ilf, n_eif = sum(c["ILF"].values()), sum(c["EIF"].values())
    n_alg = len(ALGORITHMS)
    ufep = n_ei * 4 + n_eo * 5 + n_eq * 4 + n_ilf * 7 + n_eif * 7 + n_alg * 3
    vaf = FPA["vaf"]
    out["fep"] = {
        "counts": {"EI": n_ei, "EO": n_eo, "EQ": n_eq, "ILF": n_ilf, "EIF": n_eif, "ALG": n_alg},
        "ufep": ufep, "vaf": vaf, "afep": ufep * vaf,
        "ufep_alg_min": ufep - n_alg * 3 + n_alg * 1, "ufep_alg_max": ufep - n_alg * 3 + n_alg * 10,
        "without_alg": ufep - n_alg * 3,
    }

    # Object points
    by_ctrl = defaultdict(list)
    for r in TRANS:
        by_ctrl[r["controller"]].append(r)
    screens = []
    for ctrl, rows in sorted(by_ctrl.items()):
        views = len(rows)
        files = set()
        for r in rows:
            files.update(f for f in r["files"].split("; ") if f)
        tables = len(files)
        row = 0 if views < 3 else 1 if views <= 7 else 2
        col = 0 if tables < 4 else 1 if tables < 8 else 2
        lv = SCREEN_MATRIX[(row, col)]
        screens.append({"controller": ctrl, "views": views, "tables": tables, "level": lv, "weight": SCREEN_W[lv]})
    screen_pts = sum(s["weight"] for s in screens)
    report_pts = EMAIL_TEMPLATES * REPORT_W["s"] + REPORT_W["s"]  # шаблони листів + рахунок-фактура
    gl3_n = sum(n for _, n in GL3)
    op = screen_pts + report_pts + gl3_n * GL3_W
    out["op"] = {
        "screens": screens, "screen_counts": Counter(s["level"] for s in screens), "screen_pts": screen_pts,
        "reports": EMAIL_TEMPLATES + 1, "report_pts": report_pts, "gl3": gl3_n, "gl3_pts": gl3_n * GL3_W, "op": op,
        "effort": {k: {"effort": op / v, "prod": v} for k, v in PROD.items()},
    }
    out["op"]["screen_counts"] = dict(out["op"]["screen_counts"])

    # UCP, метод 1
    uaw = sum(w for _, w, _ in ACTORS)
    ctrl_uc = {c_: uc for uc, (cs, _) in UC.items() for c_ in cs}
    ops = defaultdict(dict)  # UC -> {ключ операції: транзакція}
    for r in TRANS:
        uc = ctrl_uc[r["controller"]]
        key = (r["http"], normalize(r["path"]))
        prev = ops[uc].get(key)
        if prev is None or int(r["ufp"]) > int(prev["ufp"]):
            ops[uc][key] = r
    ucs = []
    for uc, (cs, actors) in UC.items():
        n = len(ops[uc])
        lv, w = ("s", 5) if n <= 3 else ("m", 10) if n <= 7 else ("d", 15)
        ucs.append({"name": uc, "actors": actors, "transactions": n, "level": lv, "weight": w})
    uucw = sum(u["weight"] for u in ucs)
    uucp = uaw + uucw
    tf = sum(w * v for _, w, v, _ in TECH)
    ef_sum = sum(w * v for _, w, v, _ in ENV)
    tcf = 0.6 + 0.01 * tf
    ef = 1.4 - 0.03 * ef_sum
    ucp = uucp * tcf * ef
    out["ucp"] = {
        "uaw": uaw, "uucw": uucw, "uucp": uucp, "tfactor": tf, "tcf": tcf, "efactor": ef_sum, "ef": ef, "ucp": ucp,
        "use_cases": ucs, "uc_counts": dict(Counter(u["level"] for u in ucs)),
        "hours": {"20": ucp * 20, "36": ucp * 36},
    }

    # Чутливість до дрібності варіантів використання: один варіант на контролер
    per_ctrl = defaultdict(dict)
    for r in TRANS:
        per_ctrl[r["controller"]][(r["http"], normalize(r["path"]))] = r
    cnt_lv = Counter("s" if len(v) <= 3 else "m" if len(v) <= 7 else "d" for v in per_ctrl.values())
    uucw_fine = 5 * cnt_lv["s"] + 10 * cnt_lv["m"] + 15 * cnt_lv["d"]
    ucp_fine = (uaw + uucw_fine) * tcf * ef
    out["ucp_fine"] = {"use_cases": len(per_ctrl), "counts": dict(cnt_lv), "uucw": uucw_fine, "ucp": ucp_fine, "effort_pm_20": ucp_fine * 20 / HOURS_PM}

    # UCP, метод 2: підрахунок за FP на рівні варіантів використання (без дублів версій і шляхів)
    dedup = [r for uc in ops.values() for r in uc.values()]
    cnt = {t: {lv: sum(1 for r in dedup if r["type"] == t and r["level"] == lv[0].upper()) for lv in "lah"} for t in ("EI", "EO", "EQ")}
    W = {"EI": (3, 4, 6), "EO": (4, 5, 7), "EQ": (3, 4, 6)}
    tr_ufp = sum(int(r["ufp"]) for r in dedup)
    data_ufp = FPA["subtotals"]["ILF"] + FPA["subtotals"]["EIF"]
    ufp2 = tr_ufp + data_ufp
    out["ucp2"] = {
        "operations": len(dedup), "by_type": dict(Counter(r["type"] for r in dedup)), "tr_ufp": tr_ufp, "data_ufp": data_ufp,
        "ufp": ufp2, "vaf": vaf, "afp": ufp2 * vaf, "fp3_afp": FPA["afp"],
    }

    # Економіка
    def eco(effort_pm):
        return {"effort_pm": effort_pm, "cost_usd": effort_pm * SALARY, "cost_uah": effort_pm * SALARY * RATE}

    out["economy"] = {
        "salary": SALARY, "rate": RATE, "hours_pm": HOURS_PM,
        "fp3": eco(FPA["economy"]["productivity"]["effort"]),
        "cocomo_loc": eco(FPA["economy"]["cocomo_measured"]["effort"]),
        "fep": eco(out["fep"]["afep"] / 10.4),
        "op": eco(out["op"]["effort"]["номінальна"]["effort"]),
        "ucp20": eco(ucp * 20 / HOURS_PM),
        "ucp36": eco(ucp * 36 / HOURS_PM),
        "ucp2": eco(out["ucp2"]["afp"] / 10.4),
    }
    (HERE / "points.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    f = out["fep"]
    print("FeP:", f["counts"], "UFeP", f["ufep"], "AFeP", round(f["afep"], 1), "діапазон алгоритмів", f["ufep_alg_min"], f["ufep_alg_max"])
    o = out["op"]
    print("OP: екранів", len(screens), o["screen_counts"], o["screen_pts"], "звітів", o["reports"], o["report_pts"], "3GL", o["gl3"], o["gl3_pts"], "OP", o["op"])
    print("   ефективність:", {k: round(v["effort"], 1) for k, v in o["effort"].items()})
    u = out["ucp"]
    print("UCP:", "UAW", u["uaw"], "UUCW", u["uucw"], u["uc_counts"], "TF", u["tfactor"], "TCF", round(u["tcf"], 3), "EF", round(u["ef"], 3), "UCP", round(u["ucp"], 1), {k: round(v) for k, v in u["hours"].items()})
    print("UCP2:", out["ucp2"])
    print("UCP дрібно:", out["ucp_fine"])
    for k, v in out["economy"].items():
        if isinstance(v, dict):
            print(k, {a: round(b) for a, b in v.items()})


if __name__ == "__main__":
    main()
