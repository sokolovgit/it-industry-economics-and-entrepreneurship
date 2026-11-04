"""ILF/EIF: групування JPA-сутностей Shopizer в логічні файли, підрахунок RET і DET.

Запуск: uv run --no-project --with javalang python data/ilf.py
Результат: data/ilf.json
"""

import json
from pathlib import Path

from javalang import tree as T

import javalang

from endpoints import SRC, type_names

# Індекс лише сутностей з sm-core-model: в інших модулях є DTO з тими самими іменами
INDEX = {}
for _f in (SRC / "sm-core-model" / "src" / "main").rglob("*.java"):
    try:
        _t = javalang.parse.parse(_f.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        continue
    for _, _n in _t.filter(T.ClassDeclaration):
        INDEX.setdefault(_n.name, _n)

HERE = Path(__file__).parent
EXCLUDE = {"id", "auditSection", "serialVersionUID"}
COLLECTIONS = {"List", "Set", "Map", "Collection"}

# ILF: ім'я -> сутності (кожна сутність – один RET)
ILF = {
    "Товар": ["Product", "ProductDescription", "ProductAvailability", "ProductPrice", "ProductPriceDescription", "DigitalProduct", "ProductRelationship"],
    "Зображення товару": ["ProductImage", "ProductImageDescription"],
    "Опції товару": ["ProductOption", "ProductOptionDescription", "ProductOptionValue", "ProductOptionValueDescription", "ProductOptionSet", "ProductAttribute"],
    "Варіанти товару": ["ProductVariation", "ProductVariant", "ProductVariantGroup", "ProductVariantImage", "ProductVariantImageDescription"],
    "Тип товару": ["ProductType", "ProductTypeDescription"],
    "Виробник": ["Manufacturer", "ManufacturerDescription"],
    "Відгук про товар": ["ProductReview", "ProductReviewDescription"],
    "Категорія": ["Category", "CategoryDescription"],
    "Каталог": ["Catalog", "CatalogCategoryEntry", "CatalogDescription"],
    "Контент": ["Content", "ContentDescription"],
    "Клієнт": ["Customer", "CustomerAttribute", "UserConnection"],
    "Опції клієнта": ["CustomerOption", "CustomerOptionDescription", "CustomerOptionValue", "CustomerOptionValueDescription", "CustomerOptionSet"],
    "Відгук клієнта": ["CustomerReview", "CustomerReviewDescription"],
    "Магазин": ["MerchantStore"],
    "Замовлення": ["Order", "OrderTotal", "OrderAttribute", "OrderProduct", "OrderProductAttribute", "OrderProductPrice", "OrderProductDownload", "OrderStatusHistory", "OrderAccount", "OrderAccountProduct", "FileHistory"],
    "Платіжна транзакція": ["Transaction"],
    "Кошик": ["ShoppingCart", "ShoppingCartItem", "ShoppingCartAttributeItem"],
    "Доставка": ["ShippingOrigin", "Quote"],
    "Податки": ["TaxClass", "TaxRate", "TaxRateDescription"],
    "Користувач": ["User", "Group", "Permission"],
    "Інтеграційний модуль": ["IntegrationModule"],
    "Конфігурація": ["MerchantConfiguration", "SystemConfiguration"],
    "Підписка": ["Optin", "CustomerOptin"],
    "Журнал і сповіщення": ["MerchantLog", "SystemNotification"],
    "Довідники": ["Country", "CountryDescription", "Zone", "ZoneDescription", "Currency", "Language", "GeoZone", "GeoZoneDescription"],
}

# Файлове сховище – не сутності JPA: файл і його метадані (ім'я, тип, каталог, розмір, власник, вміст, магазин)
FILE_STORAGE = {"ret": 2, "det": 7, "entities": ["Зображення (товару)", "Файл (контенту)"]}

# EIF: дані, що підтримуються поза застосунком. RET, DET – за інтерфейсами в sm-core
EIF = {
    "Тарифи перевізників (UPS, USPS)": {"ret": 2, "det": 8, "note": "пропозиція доставки і послуга: код, назва, ціна, валюта, термін, вага, пункти відправлення і призначення"},
    "Платіжні шлюзи (Stripe, PayPal, Braintree, BeanStream)": {"ret": 2, "det": 12, "note": "запит і відповідь шлюзу: ідентифікатор, статус, сума, валюта, токен, код помилки"},
}

RET_DET = {  # рядок RET, стовпець DET: (1-19, 20-50, 51+)
    1: ("L", "L", "A"),
    2: ("L", "A", "H"),
    6: ("A", "H", "H"),
}


def ilf_level(ret: int, det: int) -> str:
    row = RET_DET[1 if ret == 1 else 2 if ret <= 5 else 6]
    return row[0 if det <= 19 else 1 if det <= 50 else 2]


def entity_det(name: str) -> int:
    cls = INDEX.get(name)
    if cls is None:
        raise SystemExit(f"немає класу {name}")
    total = 0
    chain = [cls]
    parent = getattr(cls, "extends", None)
    while parent is not None and parent.name in INDEX:
        chain.append(INDEX[parent.name])
        parent = getattr(INDEX[parent.name], "extends", None)
    for c in chain:
        for m in c.body:
            if not isinstance(m, T.FieldDeclaration) or "static" in m.modifiers:
                continue
            anns = {a.name for a in (m.annotations or [])}
            if "Transient" in anns:
                continue
            names = type_names(m.type)
            if m.type.name in COLLECTIONS:
                continue
            emb = INDEX.get(m.type.name)
            embedded = emb is not None and any(a.name == "Embeddable" for a in (emb.annotations or []))
            for d in m.declarators:
                if d.name in EXCLUDE:
                    continue
                total += entity_det(m.type.name) if embedded else 1
    return total


def main() -> None:
    result = {"ilf": {}, "eif": EIF, "file_storage": FILE_STORAGE}
    assigned = set()
    for name, ents in ILF.items():
        det = sum(entity_det(e) for e in ents) + 2  # +2: дата створення і зміни (AuditSection)
        ret = len(ents)
        result["ilf"][name] = {"entities": ents, "ret": ret, "det": det, "level": ilf_level(ret, det)}
        assigned.update(ents)
    r, d = FILE_STORAGE["ret"], FILE_STORAGE["det"]
    result["ilf"]["Файлове сховище"] = {"entities": FILE_STORAGE["entities"], "ret": r, "det": d, "level": ilf_level(r, d)}
    for name, e in EIF.items():
        e["level"] = ilf_level(e["ret"], e["det"])
    all_entities = {p.stem for p in (SRC / "sm-core-model" / "src" / "main").rglob("*.java") if "@Entity" in p.read_text(encoding="utf-8", errors="replace")}
    result["unassigned"] = sorted(all_entities - assigned - {"Description"})
    (HERE / "ilf.json").write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    for n, v in result["ilf"].items():
        print(f"{n:24} RET {v['ret']:2} DET {v['det']:3} {v['level']}")
    print("не віднесено:", result["unassigned"])
    print("EIF:", {k: v["level"] for k, v in EIF.items()})


if __name__ == "__main__":
    main()
