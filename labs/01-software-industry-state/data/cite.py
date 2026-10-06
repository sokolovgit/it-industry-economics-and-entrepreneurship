"""report.src.md -> report.md: ключі [@Key] стають номерами за порядком першої згадки.

Список джерел генерується лише з тих ключів, що згадані в тексті, тож нумерація
не збивається після правок і в списку немає джерел без посилань.
"""

import re
from pathlib import Path

REPORT = Path(__file__).parent.parent / "docs" / "report"
D = "дата звернення: 04.10.2026"

SOURCES = {
    "Kitchenham2007": "Kitchenham B., Charters S. Guidelines for performing Systematic Literature Reviews in Software Engineering : EBSE Technical Report EBSE-2007-01. Keele University and Durham University, 2007. 65 p.",
    "Page2021": f"Page M. J., McKenzie J. E., Bossuyt P. M. et al. The PRISMA 2020 statement: an updated guideline for reporting systematic reviews. BMJ. 2021. Vol. 372. n71. DOI: 10.1136/bmj.n71. URL: https://www.prisma-statement.org/ ({D}).",
    "Priem2022": f"Priem J., Piwowar H., Orr R. OpenAlex: A fully-open index of scholarly works, authors, venues, institutions, and concepts. arXiv:2205.01833. 2022. URL: https://openalex.org/ ({D}).",
    "Pearce2022": f"Pearce H., Ahmad B., Tan B., Dolan-Gavitt B., Karri R. Asleep at the Keyboard? Assessing the Security of GitHub Copilot's Code Contributions. 2022 IEEE Symposium on Security and Privacy (SP). 2022. URL: https://arxiv.org/abs/2108.09293 ({D}).",
    "Ziegler2022": f"Ziegler A., Kalliamvakou E., Simister S. et al. Productivity Assessment of Neural Code Completion. MAPS 2022: Proceedings of the 6th ACM SIGPLAN International Symposium on Machine Programming. 2022. URL: https://arxiv.org/abs/2205.06537 ({D}).",
    "Peng2023": f"Peng S., Kalliamvakou E., Cihon P., Demirer M. The Impact of AI on Developer Productivity: Evidence from GitHub Copilot. arXiv:2302.06590. 2023. URL: https://arxiv.org/abs/2302.06590 ({D}).",
    "Perry2023": f"Perry N., Srivastava M., Kumar D., Boneh D. Do Users Write More Insecure Code with AI Assistants? CCS '23: Proceedings of the 2023 ACM SIGSAC Conference on Computer and Communications Security. 2023. P. 2785–2799. URL: https://arxiv.org/abs/2211.03622 ({D}).",
    "Fu2023": f"Fu Y., Liang P., Tahir A., Li Z. Security Weaknesses of Copilot-Generated Code in GitHub Projects: An Empirical Study. arXiv:2310.02059. 2023. URL: https://arxiv.org/abs/2310.02059 ({D}).",
    "Chatterjee2024": f"Chatterjee S., Liu C. L., Rowland G., Hogarth T. The Impact of AI Tool on Engineering at ANZ Bank: An Empirical Study on GitHub Copilot within Corporate Environment. arXiv:2402.05636. 2024. URL: https://arxiv.org/abs/2402.05636 ({D}).",
    "Song2024": f"Song F., Agarwal A., Wen W. The Impact of Generative AI on Collaborative Open-Source Software Development: Evidence from GitHub Copilot. arXiv:2410.02091. 2024. URL: https://arxiv.org/abs/2410.02091 ({D}).",
    "Quispe2024": f"Quispe A. Q., Grijalba R. Impact of the Availability of ChatGPT on Software Development: A Synthetic Difference in Differences Estimation using GitHub Data. arXiv:2406.11046. 2024. URL: https://arxiv.org/abs/2406.11046 ({D}).",
    "Cui2025": f"Cui K. Z., Demirer M., Jaffe S., Musolff L., Peng S., Salz T. The Effects of Generative AI on High-Skilled Work: Evidence from Three Field Experiments with Software Developers. Management Science. 2026. DOI: 10.1287/mnsc.2025.00535. URL: https://economics.mit.edu/sites/default/files/inline-files/draft_copilot_experiments.pdf ({D}).",
    "Paradis2025": f"Paradis E., Grey K., Madison Q. et al. How much does AI impact development speed? An enterprise-based randomized controlled trial. arXiv:2410.12944. 2024. URL: https://arxiv.org/abs/2410.12944 ({D}).",
    "Becker2025": f"Becker J., Rush N., Barnes E., Rein D. Measuring the Impact of Early-2025 AI on Experienced Open-Source Developer Productivity. arXiv:2507.09089. 2025. URL: https://arxiv.org/abs/2507.09089 ({D}).",
    "Stray2026": f"Stray V., Brandtzæg E. G., Wivestad V. T., Barbala A. Developer Productivity With and Without GitHub Copilot: A Longitudinal Mixed-Methods Case Study. Proceedings of the 59th Hawaii International Conference on System Sciences. 2026. DOI: 10.24251/hicss.2026.880 ({D}).",
    "Heilman2026": f"Heilman A., Kyllo A., Murphy-Hill E. R. GitHub Copilot and Developer Productivity: An Observational Dose-Response Analysis. arXiv:2606.00438. 2026. DOI: 10.48550/arxiv.2606.00438 ({D}).",
    "Borg2026": f"Borg M., Hewett D., Hagatulah N., Couderc N. Echoes of AI: Investigating the downstream effects of AI assistants on software maintainability. Empirical Software Engineering. 2026. DOI: 10.1007/s10664-026-10889-1 ({D}).",
    "Hoffmann2024": f"Hoffmann M., Boysel S., Nagle F., Peng S., Xu K. Generative AI and the Nature of Work : Harvard Business School Working Paper 25-021. 2024. URL: https://www.hbs.edu/ris/download.aspx?name=25-021.pdf ({D}).",
    "Weber2024": f"Weber T., Brandmaier M., Schmidt A., Mayer S. Significant Productivity Gains through Programming with Large Language Models. Proceedings of the ACM on Human-Computer Interaction. 2024. Vol. 8, EICS. Art. 256. DOI: 10.1145/3661145 ({D}).",
    "He2026": f"He H., Miller C., Agarwal S., Kästner C., Vasilescu B. Speed at the Cost of Quality: How Cursor AI Increases Short-Term Velocity and Long-Term Complexity in Open-Source Projects. arXiv:2511.04427. 2025. URL: https://arxiv.org/abs/2511.04427 ({D}).",
    "Daniotti2026": f"Daniotti S., Wachs J., Feng X., Neffke F. Who is using AI to code? Global diffusion and impact of generative AI. Science. 2026. DOI: 10.1126/science.adz9311. URL: https://arxiv.org/abs/2506.08945 ({D}).",
    "Maier2026": f"Maier S., Gunzenhäuser M., Schweisthal J., Schneider M. A meta-analysis of the effect of generative AI on productivity and learning in programming. arXiv:2605.04779. 2026. URL: https://arxiv.org/abs/2605.04779 ({D}).",
    "SO2023": f"Stack Overflow Developer Survey 2023. Stack Overflow. URL: https://survey.stackoverflow.co/2023/ ({D}).",
    "SO2024": f"Stack Overflow Developer Survey 2024: AI. Stack Overflow. URL: https://survey.stackoverflow.co/2024/ai ({D}).",
    "SO2025": f"Stack Overflow Developer Survey 2025: AI. Stack Overflow. URL: https://survey.stackoverflow.co/2025/ai ({D}).",
    "DORA2024": f"Accelerate State of DevOps Report 2024. DORA, Google Cloud. URL: https://services.google.com/fh/files/misc/2024_final_dora_report.pdf ({D}).",
    "DORA2025": f"Announcing the 2025 DORA Report: State of AI-assisted Software Development. Google Cloud Blog. 2025. URL: https://cloud.google.com/blog/products/ai-machine-learning/announcing-the-2025-dora-report ({D}).",
    "JetBrains2025": f"The State of Developer Ecosystem 2025. JetBrains Research Blog. 2025. URL: https://blog.jetbrains.com/research/2025/10/state-of-developer-ecosystem-2025/ ({D}).",
    "JetBrains2026": f"Which AI Coding Tools Do Developers Actually Use at Work? JetBrains Research Blog. 2026. URL: https://blog.jetbrains.com/research/2026/04/which-ai-coding-tools-do-developers-actually-use-at-work/ ({D}).",
    "GitClear2025": f"AI Copilot Code Quality: 2025 Look Back at 12 Months of Data. GitClear. 2025. URL: https://www.gitclear.com/ai_assistant_code_quality_2025_research ({D}).",
    "Uplevel2024": f"AI Won't Solve Your Developer Productivity Problems for You. Uplevel. 18.10.2024. URL: https://uplevelteam.com/blog/ai-for-developer-productivity ({D}).",
    "METR2026": f"We are Changing our Developer Productivity Experiment Design. METR. 24.02.2026. URL: https://metr.org/blog/2026-02-24-uplift-update/ ({D}).",
    "CopilotGA2022": f"GitHub Copilot is generally available to all developers. The GitHub Blog. 21.06.2022. URL: https://github.blog/news-insights/product-news/github-copilot-is-generally-available-to-all-developers/ ({D}).",
    "CopilotBusiness": f"GitHub Copilot is generally available for businesses. The GitHub Blog. 2023. URL: https://github.blog/news-insights/product-news/github-copilot-is-generally-available-for-businesses/ ({D}).",
    "CopilotEnterprise": f"GitHub Copilot Enterprise is now generally available. The GitHub Blog. 27.02.2024. URL: https://github.blog/news-insights/product-news/github-copilot-enterprise-is-now-generally-available/ ({D}).",
    "CopilotBilling2026": f"GitHub Copilot is moving to usage-based billing. The GitHub Blog. 2026. URL: https://github.blog/news-insights/company-news/github-copilot-is-moving-to-usage-based-billing/ ({D}).",
    "CursorPricing": f"Pricing. Cursor. URL: https://cursor.com/pricing ({D}).",
    "ClaudePricing": f"Pricing. Claude. URL: https://claude.com/pricing ({D}).",
    "DOU2026": f"Зарплати розробників – літо 2026. DOU. 13.07.2026. URL: https://dou.ua/lenta/articles/salary-report-devs-summer-2026/ ({D}).",
    "DOU2023": f"Зарплати розробників – літо 2023. DOU. 2023. URL: https://dou.ua/lenta/articles/salary-report-devs-summer-2023/ ({D}).",
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
    print(
        f"посилань: {len(order)}; не використано: {sorted(set(SOURCES) - set(order))}"
    )


if __name__ == "__main__":
    main()
