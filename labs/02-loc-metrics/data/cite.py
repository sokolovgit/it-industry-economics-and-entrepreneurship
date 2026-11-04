"""report.src.md -> report.md: ключі [@Key] стають номерами за порядком першої згадки."""

import re
from pathlib import Path

REPORT = Path(__file__).parent.parent / "docs" / "report"
D = "дата звернення: 04.11.2026"

SOURCES = {
    "Shopizer": f"Shopizer: Java open source e-commerce software. URL: https://github.com/shopizer-ecommerce/shopizer, коміт 6a4a0a6 від 23.03.2025 ({D}).",
    "Cloc": f"Adler D. cloc: Count Lines of Code, версія 2.10. URL: https://github.com/AlDanial/cloc ({D}).",
    "Park1992": f"Park R. E. Software Size Measurement: A Framework for Counting Source Statements : CMU/SEI-92-TR-020. Software Engineering Institute, Carnegie Mellon University, 1992. URL: https://sei.cmu.edu/library/software-size-measurement-a-framework-for-counting-source-statements ({D}).",
    "Javalang": f"javalang: Pure Python Java parser and tools. URL: https://github.com/c2nes/javalang ({D}).",
    "Boehm1981": "Boehm B. W. Software Engineering Economics. Englewood Cliffs, NJ : Prentice-Hall, 1981. 767 p.",
    "Jones2017": f"Jones C. Software Economics and Function Point Metrics: Thirty years of IFPUG Progress, версія 10.0. Namcook Analytics, 14.04.2017. URL: https://www.ifpug.org/wp-content/uploads/2017/04/IYSM.-Thirty-years-of-IFPUG.-Software-Economics-and-Function-Point-Metrics-Capers-Jones.pdf ({D}).",
    "QSM": f"Function Point Languages Table, версія 5.0. QSM. URL: https://www.qsm.com/resources/function-point-languages-table ({D}).",
    "DOU2026": f"Зарплати українських розробників – літо 2026. DOU. 13.07.2026. URL: https://dou.ua/lenta/articles/salary-report-devs-summer-2026/ ({D}).",
    "NBU": f"Офіційний курс гривні щодо іноземних валют на 04.11.2026: долар США 45.666 UAH. Національний банк України. URL: https://bank.gov.ua/NBUStatService/v1/statdirectory/exchange?valcode=USD&date=20261104&json ({D}).",
}


def main():
    src = (REPORT / "report.src.md").read_text(encoding="utf-8")
    order: list[str] = []

    def num(key: str) -> str:
        if key not in SOURCES:
            raise SystemExit(f"невідоме джерело: {key}")
        if key not in order:
            order.append(key)
        return str(order.index(key) + 1)

    body = re.sub(
        r"\[@([\w,;\s@]+)\]",
        lambda m: (
            "["
            + ", ".join(num(k.strip().lstrip("@")) for k in re.split(r"[,;]", m.group(1)))
            + "]"
        ),
        src,
    )
    refs = "\n".join(f"{i}. {SOURCES[k]}" for i, k in enumerate(order, start=1))
    body = body.replace("<!-- SOURCES -->", refs)
    (REPORT / "report.md").write_text(body, encoding="utf-8")
    print(f"посилань: {len(order)}; не використано: {sorted(set(SOURCES) - set(order))}")


if __name__ == "__main__":
    main()
