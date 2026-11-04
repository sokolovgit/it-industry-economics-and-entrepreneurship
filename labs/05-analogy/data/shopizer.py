"""Атрибути «нового» проєкту Shopizer тими ж способами, що й для аналогів (collect.py)."""

import json
import re
import subprocess
from pathlib import Path

HERE = Path(__file__).parent
D = HERE.parent.parent / "02-loc-metrics" / "data" / "src" / "shopizer"
MAP = re.compile(rb"@(Get|Post|Put|Delete|Patch|Request)Mapping")
BEAN = re.compile(rb"@(Service|Component|Repository|RestController|Controller|Configuration)\b")

c = json.loads(subprocess.run(["cloc", "--json", "--by-file", "--include-lang=Java", "--quiet", str(D)], capture_output=True, text=True).stdout)
files = {k: v for k, v in c.items() if k not in ("header", "SUM")}
modules = deps = beans = maps = 0
for p in D.rglob("*"):
    if ".git" in p.parts or not p.is_file():
        continue
    if p.name == "pom.xml":
        modules += 1
        deps += p.read_bytes().count(b"<dependency>")
    elif p.name.endswith(".java"):
        b = p.read_bytes()
        beans += len(BEAN.findall(b))
        maps += len(MAP.findall(b))
out = {
    "repo": "shopizer-ecommerce/shopizer", "commit": "6a4a0a6", "java_files": len(files),
    "code": sum(v["code"] for v in files.values()), "comment": sum(v["comment"] for v in files.values()),
    "test": sum(v["code"] for k, v in files.items() if re.search(r"/(test|tests)/|Test\.java$", k)),
    "modules": modules, "deps": deps, "beans": beans, "endpoints": maps,
}
(HERE / "shopizer.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print(out)
