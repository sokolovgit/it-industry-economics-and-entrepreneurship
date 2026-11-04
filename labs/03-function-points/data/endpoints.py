"""Виділення транзакцій REST API Shopizer: ендпоінти, DTO, використані сервіси.

Запуск: uv run --no-project --with javalang python data/endpoints.py
Результат: data/endpoints.json
"""

import json
import re
from pathlib import Path

import javalang
from javalang import tree as T

HERE = Path(__file__).parent
SRC = HERE.parent.parent / "02-loc-metrics" / "data" / "src" / "shopizer"
API = SRC / "sm-shop" / "src" / "main" / "java"
MODEL_ROOTS = [SRC / m / "src" / "main" / "java" for m in ("sm-shop-model", "sm-shop", "sm-core-model")]

HTTP = {"GetMapping": "GET", "PostMapping": "POST", "PutMapping": "PUT", "PatchMapping": "PATCH", "DeleteMapping": "DELETE"}
SKIP_PARAMS = {"store", "lang", "page", "count", "start", "max", "order", "orderby"}
SIMPLE = {
    "String", "int", "Integer", "long", "Long", "double", "Double", "float", "Float", "boolean", "Boolean",
    "BigDecimal", "Date", "LocalDate", "LocalDateTime", "byte", "Byte", "short", "Short", "char", "Character",
    "Object", "MultipartFile", "BigInteger", "InputStream", "byte[]",
}
COLLECTIONS = {"List", "Set", "Collection", "Map", "Optional", "ResponseEntity", "Iterable", "ArrayList", "HashSet"}


def parse(path: Path):
    return javalang.parse.parse(path.read_text(encoding="utf-8", errors="replace"))


def build_class_index():
    index = {}
    for root in MODEL_ROOTS:
        for f in root.rglob("*.java"):
            try:
                tree = parse(f)
            except Exception:
                continue
            for _, node in tree.filter(T.ClassDeclaration):
                index.setdefault(node.name, node)
            for _, node in tree.filter(T.EnumDeclaration):
                index.setdefault(node.name, node)
    return index


INDEX = build_class_index()


def type_names(t) -> list[str]:
    """Імена типів без обгорток-колекцій, з аргументами generic."""
    if t is None:
        return []
    out = []
    name = t.name
    args = [a.type for a in (getattr(t, "arguments", None) or []) if hasattr(a, "type") and a.type is not None]
    if name in COLLECTIONS:
        for a in args:
            out += type_names(a)
    else:
        out.append(name + ("[]" if t.dimensions else ""))
    return out


def fields_of(cls, seen: set[str], depth: int = 0) -> int:
    """Кількість різних полів (DET) класу з вкладеними класами: кожен клас рахується один раз."""
    if cls.name in seen or depth > 4:
        return 0
    seen.add(cls.name)
    if isinstance(cls, T.EnumDeclaration):
        return 0
    total = 0
    parent = getattr(cls, "extends", None)
    if parent is not None and parent.name in INDEX:
        total += fields_of(INDEX[parent.name], seen, depth)
    for member in cls.body:
        if not isinstance(member, T.FieldDeclaration):
            continue
        if "static" in member.modifiers:
            continue
        if any(a.name in ("JsonIgnore", "Transient") for a in (member.annotations or [])):
            continue
        names = type_names(member.type)
        for decl in member.declarators:
            complex_types = [n for n in names if n in INDEX and not isinstance(INDEX[n], T.EnumDeclaration) and n not in SIMPLE]
            if complex_types:
                for n in complex_types:
                    total += fields_of(INDEX[n], seen, depth + 1)
            else:
                total += 1
    return total


def det_of_type(t) -> int:
    seen: set[str] = set()
    total = 0
    for n in type_names(t):
        if n in INDEX:
            total += fields_of(INDEX[n], seen)
        elif n not in ("void", "Void"):
            total += 1
    return total


def literal_strings(el) -> list[str]:
    if el is None:
        return []
    if isinstance(el, javalang.tree.Literal):
        return [el.value.strip('"')]
    if isinstance(el, javalang.tree.ElementArrayValue):
        return [v.value.strip('"') for v in el.values if isinstance(v, javalang.tree.Literal)]
    if isinstance(el, list):
        return [x for v in el for x in literal_strings(v)]
    return []


def annotation_pairs(ann):
    el = ann.element
    if el is None:
        return {}
    if isinstance(el, list):
        return {p.name: p.value for p in el}
    return {"value": el}


def analyze_controller(path: Path):
    tree = parse(path)
    out = []
    for _, cls in tree.filter(T.ClassDeclaration):
        class_ann = {a.name: a for a in (cls.annotations or [])}
        if not ({"RestController", "Controller"} & set(class_ann)):
            continue
        base = ""
        if "RequestMapping" in class_ann:
            base = (literal_strings(annotation_pairs(class_ann["RequestMapping"]).get("value")) or [""])[0]
        fields = {}
        for m in cls.body:
            if isinstance(m, T.FieldDeclaration):
                for d in m.declarators:
                    fields[d.name] = m.type.name
        for m in cls.body:
            if not isinstance(m, T.MethodDeclaration):
                continue
            http = None
            paths: list[str] = []
            for a in m.annotations or []:
                if a.name in HTTP:
                    http = HTTP[a.name]
                    pairs = annotation_pairs(a)
                    paths = literal_strings(pairs.get("value") or pairs.get("path"))
                elif a.name == "RequestMapping":
                    pairs = annotation_pairs(a)
                    paths = literal_strings(pairs.get("value") or pairs.get("path"))
                    meth = pairs.get("method")
                    if meth is not None:
                        mm = re.findall(r"(GET|POST|PUT|PATCH|DELETE)", str(meth))
                        http = mm[0] if mm else None
                    if http is None:
                        http = "GET"
            if http is None:
                continue
            body_type, params, path_vars = None, [], []
            for p in m.parameters:
                anns = {a.name: a for a in (p.annotations or [])}
                if "RequestBody" in anns:
                    body_type = p.type
                elif "RequestParam" in anns:
                    pairs = annotation_pairs(anns["RequestParam"])
                    nm = (literal_strings(pairs.get("value") or pairs.get("name")) or [p.name])[0]
                    if nm not in SKIP_PARAMS and p.type.name not in ("MerchantStore", "Language", "HttpServletRequest"):
                        params.append(nm)
                elif "PathVariable" in anns:
                    path_vars.append(p.name)
                elif "ModelAttribute" in anns or ("Valid" in anns and "RequestBody" not in anns):
                    if p.type.name in INDEX:
                        body_type = p.type
            used = set()
            for _, n in m.filter(T.MethodInvocation):
                if n.qualifier and n.qualifier in fields:
                    used.add(fields[n.qualifier])
            for _, n in m.filter(T.MemberReference):
                if n.qualifier and n.qualifier in fields:
                    used.add(fields[n.qualifier])
            out.append(
                {
                    "controller": cls.name,
                    "file": str(path.relative_to(API)),
                    "method": m.name,
                    "http": http,
                    "base": base,
                    "paths": [base + p for p in paths],
                    "request_type": body_type.name if body_type else None,
                    "request_det": det_of_type(body_type) if body_type else 0,
                    "params": params,
                    "path_vars": path_vars,
                    "response_type": "void" if m.return_type is None else m.return_type.name,
                    "response_det": det_of_type(m.return_type) if m.return_type else 0,
                    "uses": sorted(used),
                }
            )
    return out


def main():
    rows = []
    for f in sorted(API.rglob("*.java")):
        text = f.read_text(encoding="utf-8", errors="replace")
        if "@RestController" not in text and "@Controller" not in text:
            continue
        try:
            rows += analyze_controller(f)
        except Exception as e:
            print("FAIL", f.name, type(e).__name__, e)
    (HERE / "endpoints.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    from collections import Counter
    print(len(rows), "методів;", Counter(r["http"] for r in rows))
    print("без шляху:", sum(1 for r in rows if not r["paths"]))
    uses = Counter(u for r in rows for u in r["uses"])
    print(sorted(uses.items(), key=lambda x: -x[1]))


if __name__ == "__main__":
    main()
