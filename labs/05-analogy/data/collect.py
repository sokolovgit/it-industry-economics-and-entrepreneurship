"""Збір бази проєктів для методу аналогій: клонування, cloc, атрибути з коду, історія комітів.

Запуск: python3 data/collect.py   (потрібні git, cloc; виконується кілька хвилин)
Результат: data/projects_raw.json
Якщо projects_raw.json уже існує, кожен репозиторій перемикається на записаний у ньому коміт, щоб повторний запуск давав ті самі числа.
"""

import json
import re
import subprocess
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).parent
SRC = HERE / "src" / "analogs"
CANDIDATES = [
    "alfio-event/alf.io", "merikbest/OnlineShop", "sadatrafsanjani/Point-of-Sales", "inforkgodara/store-pos",
    "afsalashyana/Library-Assistant", "jishenghua/jshERP", "FJ-OMS/oms-erp", "getrebuild/rebuild",
    "1Panel-dev/CordysCRM", "201206030/novel", "xujeff/tianti", "diyhi/bbs", "michaelliao/itranswarp",
    "dromara/ujcms", "WuKongOpenSource/WukongCRM-11.0-JAVA", "halo-dev/halo", "RainbowForest/e-commerce-microservices",
    "shashirajraja/shopping-cart", "sajxraj/InventoryManagementSystem", "spring-petclinic/spring-petclinic-microservices",
    "spring-projects/spring-petclinic", "sqshq/piggymetrics", "traccar/traccar", "shouryaj98/Hotel-Management-Project-Java",
    "chillzhuang/SpringBlade", "harismuneer/Library-Management-System-JAVA", "hanlinag/point-of-sale-system",
    "yf-team/yf-boot", "malizhigithub/CRM", "s-pms/SPMS-Server",
]
PINNED = {}
_raw = HERE / "projects_raw.json"
if _raw.exists():
    PINNED = {r["repo"]: r["commit"] for r in json.loads(_raw.read_text(encoding="utf-8")) if r.get("commit")}
MAP = re.compile(rb"@(Get|Post|Put|Delete|Patch|Request)Mapping")
BEAN = re.compile(rb"@(Service|Component|Repository|RestController|Controller|Configuration)\b")


def sh(*cmd, cwd=None, timeout=900):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)


def collect(repo: str):
    name = repo.replace("/", "__")
    d = SRC / name
    try:
        if not d.exists():
            r = sh("git", "clone", "--filter=blob:none", "--no-checkout", f"https://github.com/{repo}.git", str(d))
            if r.returncode:
                return {"repo": repo, "error": "clone: " + r.stderr[-200:]}
        sh("git", "checkout", "--force", PINNED.get(repo, "HEAD"), cwd=d)
        head = sh("git", "rev-parse", "--short", "HEAD", cwd=d).stdout.strip()
        # cloc по файлах Java
        c = json.loads(sh("cloc", "--json", "--by-file", "--include-lang=Java", "--quiet", str(d)).stdout or "{}")
        files = {k: v for k, v in c.items() if k not in ("header", "SUM")}
        code = sum(v["code"] for v in files.values())
        comment = sum(v["comment"] for v in files.values())
        test = sum(v["code"] for k, v in files.items() if re.search(r"/(test|tests)/|Test\.java$", k))
        # атрибути з коду
        modules = deps = beans = maps = 0
        for p in d.rglob("*"):
            if ".git" in p.parts or not p.is_file():
                continue
            n = p.name
            if n == "pom.xml":
                modules += 1
                deps += p.read_bytes().count(b"<dependency>")
            elif n in ("build.gradle", "build.gradle.kts"):
                modules += 1
                deps += len(re.findall(rb"^\s*(implementation|api|compile|runtimeOnly|testImplementation)\b", p.read_bytes(), re.M))
            elif n.endswith(".java"):
                b = p.read_bytes()
                beans += len(BEAN.findall(b))
                maps += len(MAP.findall(b))
        # історія: активні розробники за місяць
        log = sh("git", "log", "--format=%aI|%ae", cwd=d).stdout.splitlines()
        am = defaultdict(set)
        authors = set()
        dates = []
        for line in log:
            if "|" not in line:
                continue
            dt, em = line.split("|", 1)
            am[dt[:7]].add(em)
            authors.add(em)
            dates.append(dt)
        months = sum(len(v) for v in am.values())
        return {
            "repo": repo, "commit": head, "java_files": len(files), "code": code, "comment": comment, "test": test,
            "modules": modules, "deps": deps, "beans": beans, "endpoints": maps,
            "commits": len(log), "authors": len(authors), "contributor_months": months,
            "first": min(dates)[:10] if dates else None, "last": max(dates)[:10] if dates else None,
        }
    except Exception as e:  # noqa: BLE001
        return {"repo": repo, "error": f"{type(e).__name__}: {e}"}


def main():
    SRC.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(6) as ex:
        rows = list(ex.map(collect, CANDIDATES))
    (HERE / "projects_raw.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    for r in rows:
        if "error" in r:
            print("ERR", r["repo"], r["error"][:100])
        else:
            print(f"{r['repo']:50} code {r['code']:7} mod {r['modules']:3} dep {r['deps']:4} bean {r['beans']:4} ep {r['endpoints']:4} commits {r['commits']:6} cm {r['contributor_months']:5} {r['first']}..{r['last']}")


if __name__ == "__main__":
    main()
