"""Вимірювання розміру Shopizer: фізичні рядки, рядки коду, коментарі (cloc) і логічні рядки (за AST).

Запуск: uv run --no-project --with javalang python data/measure.py
Результат: data/loc.json
"""

import json
import subprocess
from pathlib import Path

import javalang
from javalang import tree as T

HERE = Path(__file__).parent
SRC = HERE / "src" / "shopizer"
MODULES = ["sm-core-model", "sm-core-modules", "sm-core", "sm-shop-model", "sm-shop"]

# Логічний рядок – один оператор або одна декларація (імпорт, пакет, клас, метод, поле, змінна).
DECLARATIONS = (
    T.FieldDeclaration,
    T.MethodDeclaration,
    T.ConstructorDeclaration,
    T.ClassDeclaration,
    T.InterfaceDeclaration,
    T.EnumDeclaration,
    T.AnnotationDeclaration,
    T.EnumConstantDeclaration,
    T.LocalVariableDeclaration,
    T.Import,
    T.PackageDeclaration,
)


def cloc(*paths: Path, java_only: bool = False) -> dict:
    cmd = ["cloc", "--json", "--quiet"]
    if java_only:
        cmd.append("--include-lang=Java")
    cmd += [str(p) for p in paths]
    out = subprocess.run(cmd, capture_output=True, text=True, check=True).stdout
    data = json.loads(out) if out.strip() else {}
    data.pop("header", None)
    return data


def java_totals(data: dict) -> dict:
    j = data.get("Java", {})
    return {
        "files": j.get("nFiles", 0),
        "blank": j.get("blank", 0),
        "comment": j.get("comment", 0),
        "code": j.get("code", 0),
    }


def physical_lines(files: list[Path]) -> int:
    return sum(len(f.read_bytes().splitlines()) for f in files)


def logical_lines(files: list[Path]) -> tuple[int, int]:
    total, failed = 0, 0
    for f in files:
        try:
            ast = javalang.parse.parse(f.read_text(encoding="utf-8", errors="replace"))
        except Exception:
            failed += 1
            continue
        for _, node in ast:
            if isinstance(node, DECLARATIONS) or (
                isinstance(node, T.Statement) and not isinstance(node, T.BlockStatement)
            ):
                total += 1
    return total, failed


def main() -> None:
    result: dict = {
        "commit": subprocess.run(
            ["git", "-C", str(SRC), "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
        ).stdout.strip()
    }
    result["all_languages"] = cloc(SRC)
    result["modules"] = {}
    for m in MODULES:
        for kind in ("main", "test"):
            root = SRC / m / "src" / kind
            if not root.exists():
                continue
            files = sorted(root.rglob("*.java"))
            if not files:
                continue
            c = java_totals(cloc(root, java_only=True))
            lloc, failed = logical_lines(files)
            c["physical"] = physical_lines(files)
            c["logical"] = lloc
            c["parse_failed"] = failed
            result["modules"][f"{m}/{kind}"] = c
    for kind in ("main", "test"):
        keys = [k for k in result["modules"] if k.endswith("/" + kind)]
        agg = {
            f: sum(result["modules"][k][f] for k in keys)
            for f in (
                "files",
                "blank",
                "comment",
                "code",
                "physical",
                "logical",
                "parse_failed",
            )
        }
        result[f"java_{kind}"] = agg
    (HERE / "loc.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    for k, v in result["modules"].items():
        print(
            f"{k:28} files {v['files']:4}  phys {v['physical']:6}  code {v['code']:6}  comm {v['comment']:5}  blank {v['blank']:5}  lloc {v['logical']:6}  fail {v['parse_failed']}"
        )
    for kind in ("main", "test"):
        print(kind, result[f"java_{kind}"])


if __name__ == "__main__":
    main()
