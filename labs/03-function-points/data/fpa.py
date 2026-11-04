"""Аналіз функціональних точок Shopizer: класифікація транзакцій, складність, UFP, VAF, AFP.

Запуск: python3 data/fpa.py   (після endpoints.py і ilf.py)
Результат: data/fpa.json, data/transactions.csv
"""

import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).parent
EP = json.loads((HERE / "endpoints.json").read_text(encoding="utf-8"))
ILF = json.loads((HERE / "ilf.json").read_text(encoding="utf-8"))

WEIGHTS = {"ILF": (7, 10, 15), "EIF": (5, 7, 10), "EI": (3, 4, 6), "EO": (4, 5, 7), "EQ": (3, 4, 6)}
LEVELS = {"L": 0, "A": 1, "H": 2}

# Основні логічні файли, до яких звертається контролер
CONTROLLER_FILES = {
    "FilesController": ["Файлове сховище"],
    "ImagesController": ["Файлове сховище"],
    "StoreContactRESTController": ["Магазин"],
    "SystemRESTController": ["Інтеграційний модуль"],
    "CatalogApi": ["Каталог", "Категорія"],
    "CategoryApi": ["Категорія"],
    "CacheApi": [],
    "ConfigurationsApi": ["Конфігурація"],
    "ContentAdministrationApi": ["Контент", "Файлове сховище"],
    "ContentApi": ["Контент"],
    "AuthenticateCustomerApi": ["Клієнт"],
    "CustomerApi": ["Клієнт"],
    "CustomerNewsletterApi": ["Підписка", "Клієнт"],
    "CustomerReviewApi": ["Відгук клієнта", "Клієнт"],
    "ResetCustomerPasswordApi": ["Клієнт"],
    "MarketPlaceApi": ["Магазин"],
    "OrderApi": ["Замовлення", "Клієнт"],
    "OrderPaymentApi": ["Платіжна транзакція", "Замовлення"],
    "OrderShippingApi": ["Доставка", "Кошик"],
    "OrderStatusHistoryApi": ["Замовлення"],
    "OrderTotalApi": ["Замовлення", "Кошик"],
    "PaymentApi": ["Платіжна транзакція", "Інтеграційний модуль"],
    "ProductApi": ["Товар", "Категорія"],
    "ProductAttributeOptionApi": ["Опції товару"],
    "ProductGroupApi": ["Товар"],
    "ProductImageApi": ["Зображення товару", "Товар"],
    "ProductInventoryApi": ["Товар"],
    "ProductManufacturerApi": ["Виробник"],
    "ProductPriceApi": ["Товар"],
    "ProductPropertySetApi": ["Опції товару"],
    "ProductRelationshipApi": ["Товар"],
    "ProductReviewApi": ["Відгук про товар", "Товар"],
    "ProductTypeApi": ["Тип товару"],
    "ReferencesApi": ["Довідники"],
    "SearchApi": ["Товар"],
    "SecurityApi": ["Користувач"],
    "ShippingConfigurationApi": ["Доставка", "Інтеграційний модуль"],
    "ShippingExpeditionApi": ["Доставка"],
    "ShoppingCartApi": ["Кошик", "Товар"],
    "MerchantStoreApi": ["Магазин"],
    "ContactApi": ["Магазин"],
    "ModulesApi": ["Інтеграційний модуль"],
    "OptinApi": ["Підписка"],
    "PublicConfigsApi": ["Конфігурація"],
    "SearchToolsApi": ["Товар"],
    "TaxClassApi": ["Податки"],
    "TaxRatesApi": ["Податки"],
    "AuthenticateUserApi": ["Користувач"],
    "ResetUserPasswordApi": ["Користувач"],
    "UserApi": ["Користувач"],
    "ProductApiV2": ["Товар"],
    "ProductVariantApi": ["Варіанти товару"],
    "ProductVariantGroupApi": ["Варіанти товару"],
    "ProductVariationApi": ["Варіанти товару", "Опції товару"],
}
# Додаткові файли за викликаними фасадами й сервісами
SERVICE_FILES = {
    "UserFacade": "Користувач", "UserDetailsService": "Користувач", "GroupService": "Користувач", "PermissionService": "Користувач",
    "ContentFacade": "Контент", "ContentService": "Контент", "StoreFacade": "Магазин", "MerchantStoreService": "Магазин",
    "CustomerFacade": "Клієнт", "CustomerService": "Клієнт", "ProductOptionFacade": "Опції товару", "ProductOptionSetFacade": "Опції товару",
    "OrderFacade": "Замовлення", "OrderService": "Замовлення", "ProductCommonFacade": "Товар", "ProductService": "Товар",
    "ProductFacade": "Товар", "ProductItemsFacade": "Товар", "ProductDefinitionFacade": "Товар", "ProductPriceFacade": "Товар",
    "PricingService": "Товар", "ProductInventoryFacade": "Товар", "CategoryFacade": "Категорія", "CategoryService": "Категорія",
    "TaxFacade": "Податки", "ShoppingCartFacade": "Кошик", "ShoppingCartService": "Кошик", "ShippingFacade": "Доставка",
    "ShippingService": "Доставка", "ShippingQuoteService": "Доставка", "CatalogFacade": "Каталог", "ManufacturerFacade": "Виробник",
    "ManufacturerService": "Виробник", "ProductImageService": "Зображення товару", "ProductVariantGroupFacade": "Варіанти товару",
    "ProductVariantFacade": "Варіанти товару", "ProductVariationFacade": "Варіанти товару", "ProductTypeFacade": "Тип товару",
    "PaymentService": "Платіжна транзакція", "ProductReviewService": "Відгук про товар", "SearchFacade": "Товар",
    "MarketPlaceFacade": "Магазин", "CountryService": "Довідники", "CountryFacade": "Довідники", "ZoneFacade": "Довідники",
    "CurrencyFacade": "Довідники", "LanguageFacade": "Довідники", "OptinFacade": "Підписка", "MerchantConfigurationFacade": "Конфігурація",
    "ModuleConfigurationService": "Інтеграційний модуль",
}
EIF_BY_CONTROLLER = {
    "OrderPaymentApi": ["Платіжні шлюзи (Stripe, PayPal, Braintree, BeanStream)"],
    "PaymentApi": ["Платіжні шлюзи (Stripe, PayPal, Braintree, BeanStream)"],
    "OrderShippingApi": ["Тарифи перевізників (UPS, USPS)"],
    "OrderTotalApi": ["Тарифи перевізників (UPS, USPS)"],
}
CUSTOMER_AUTH = {"AuthenticateCustomerApi", "ResetCustomerPasswordApi"}  # UserDetailsService тут обслуговує клієнтів
EXCLUDE: set[str] = set()

CALC_PATH = re.compile(r"total|quote|shipping")
AUTH_PATH = re.compile(r"authenticate|login|refresh|/search|autocomplete|/suggest")
CALC_CONTROLLERS = {"OrderTotalApi", "OrderShippingApi"}


def level(table: str, ftr: int, det: int) -> str:
    if table == "EI":
        row = 0 if ftr <= 1 else 1 if ftr == 2 else 2
        col = 0 if det <= 4 else 1 if det <= 15 else 2
        m = [("L", "L", "A"), ("L", "A", "H"), ("A", "H", "H")]
    else:  # EO і вихід EQ
        row = 0 if ftr <= 1 else 1 if ftr <= 3 else 2
        col = 0 if det <= 5 else 1 if det <= 19 else 2
        m = [("L", "L", "A"), ("L", "A", "H"), ("A", "H", "H")]
    return m[row][col]


def classify(r: dict) -> str:
    path = (r["paths"][0] if r["paths"] else "").lower()
    if r["controller"] in CALC_CONTROLLERS or CALC_PATH.search(path):
        return "EO"
    if r["controller"] == "ShoppingCartApi" and r["http"] == "GET":
        return "EO"
    if AUTH_PATH.search(path):
        return "EQ"
    return "EI" if r["http"] in ("POST", "PUT", "PATCH", "DELETE") else "EQ"


def main() -> None:
    rows = []
    for r in EP:
        if r["controller"] in EXCLUDE:
            continue
        files = set(CONTROLLER_FILES.get(r["controller"], []))
        for u in ([] if r["controller"] in CUSTOMER_AUTH else r["uses"]):
            if u in SERVICE_FILES:
                files.add(SERVICE_FILES[u])
        eifs = EIF_BY_CONTROLLER.get(r["controller"], [])
        ftr = len(files) + len(eifs)
        t = classify(r)
        n_in = len(r["params"]) + len(r["path_vars"])
        # @RequestBody у GET-методі (ProductPriceApi.get) не є вхідними даними запиту: тіло GET ігнорується
        req_det = 0 if r["http"] == "GET" else r["request_det"]
        if t == "EI":
            lv = level("EI", ftr, req_det + n_in + 1)
            det = req_det + n_in + 1
        elif t == "EO":
            det = max(r["response_det"], 1)
            lv = level("EO", ftr, det)
        else:  # EQ: більший з рівнів входу і виходу
            det_out = max(r["response_det"], 1)
            det_in = n_in + req_det
            lv = max(level("EI", ftr, max(det_in, 1)), level("EO", ftr, det_out), key=lambda x: LEVELS[x])
            det = det_out
        rows.append(
            {
                "controller": r["controller"], "method": r["method"], "http": r["http"], "path": r["paths"][0],
                "type": t, "ftr": ftr, "det": det, "level": lv, "ufp": WEIGHTS[t][LEVELS[lv]],
                "files": sorted(files) + eifs,
            }
        )
    with open(HERE / "transactions.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        for r in rows:
            w.writerow({**r, "files": "; ".join(r["files"])})

    counts = {}
    for t in ("EI", "EO", "EQ"):
        counts[t] = {lv: sum(1 for r in rows if r["type"] == t and r["level"] == lv) for lv in "LAH"}
    ilf_counts = Counter(v["level"] for v in ILF["ilf"].values())
    eif_counts = Counter(v["level"] for v in ILF["eif"].values())
    counts["ILF"] = {lv: ilf_counts.get(lv, 0) for lv in "LAH"}
    counts["EIF"] = {lv: eif_counts.get(lv, 0) for lv in "LAH"}
    sub = {k: sum(counts[k][lv] * WEIGHTS[k][LEVELS[lv]] for lv in "LAH") for k in counts}
    ufp = sum(sub.values())

    gsc = {
        "Обмін даними": 5, "Розподілена обробка даних": 3, "Продуктивність": 2, "Обмеження апаратних ресурсів": 1,
        "Транзакційне навантаження": 3, "Інтенсивність взаємодії з користувачем": 5, "Ергономіка": 3,
        "Інтенсивність зміни даних": 4, "Складність обробки": 4, "Повторне використання": 3,
        "Зручність інсталяції": 3, "Зручність адміністрування": 2, "Можливість портування": 4, "Гнучкість": 3,
    }
    tdi = sum(gsc.values())
    vaf = tdi * 0.01 + 0.65
    afp = ufp * vaf
    out = {"transactions": len(rows), "counts": counts, "subtotals": sub, "ufp": ufp, "gsc": gsc, "tdi": tdi, "vaf": vaf, "afp": afp}
    # Економічні характеристики за AFP
    pr2 = json.loads((HERE.parent.parent / "02-loc-metrics" / "data" / "economy.json").read_text(encoding="utf-8"))
    loc2 = json.loads((HERE.parent.parent / "02-loc-metrics" / "data" / "loc.json").read_text(encoding="utf-8"))
    salary, rate = pr2["salary_usd"], pr2["usd_uah"]
    lm, fp_month = 53.33, 10.40  # Jones 2017, табл. 16: Java
    lloc_est = afp * lm
    code_ratio = loc2["java_main"]["code"] / loc2["java_main"]["logical"]
    kloc_est = lloc_est * code_ratio / 1000
    semi = dict(a=3.0, b=1.12, c=2.5, d=0.35)

    def cocomo(kloc):
        e = semi["a"] * kloc ** semi["b"]
        return {"effort": e, "schedule": semi["c"] * e ** semi["d"]}

    c_fp = cocomo(kloc_est)
    eco = {
        "lloc_est": lloc_est, "kloc_est": kloc_est, "lloc_measured": loc2["java_main"]["logical"],
        "sloc_per_fp_measured": loc2["java_main"]["logical"] / afp,
        "fp_backfired_pr2": pr2["backfired_fp"],
        "productivity": {"effort": afp / fp_month},
        "cocomo_from_fp": c_fp,
        "cocomo_measured": {"effort": pr2["by_type"]["Напіврозділений"]["effort_pm"], "schedule": pr2["by_type"]["Напіврозділений"]["schedule_months"]},
    }
    eco["productivity"]["schedule"] = None
    for k in ("productivity", "cocomo_from_fp", "cocomo_measured"):
        eco[k]["cost_usd"] = eco[k]["effort"] * salary
        eco[k]["cost_uah"] = eco[k]["cost_usd"] * rate
        eco[k]["cost_per_fp"] = eco[k]["cost_usd"] / afp
    out["economy"] = eco
    (HERE / "fpa.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("транзакцій:", len(rows), Counter(r["type"] for r in rows))
    for k, v in counts.items():
        print(k, v, "->", sub[k])
    print("UFP", ufp, "TDI", tdi, "VAF", round(vaf, 2), "AFP", round(afp, 1))
    print({k: (round(v, 1) if isinstance(v, float) else v) for k, v in eco.items() if not isinstance(v, dict)})
    for k in ("productivity", "cocomo_from_fp", "cocomo_measured"):
        print(k, {a: round(b, 1) for a, b in eco[k].items() if b is not None})
    by_ctrl = defaultdict(lambda: Counter())
    for r in rows:
        by_ctrl[r["controller"]][r["type"]] += 1


if __name__ == "__main__":
    main()
