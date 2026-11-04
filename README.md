# Економіка ІТ-індустрії та підприємництво

КПІ ім. Ігоря Сікорського, ФІОТ, 4 курс, 1 семестр.

- Лектор: Сидоров М. О.; практичні: Жебка В. В.
- Контроль: екзамен

## Структура

| Тека | Зміст |
|---|---|
| [`docs/`](docs/) | матеріали курсу: силабус, завдання ПР1–ПР7, `labs/dependencies.md` – залежності між роботами |
| [`labs/01-software-industry-state/`](labs/01-software-industry-state/) | ПР1: SLR про економічну ефективність AI-асистентів у розробці ПЗ (звіт, презентація, скрипти пошуку) |
| [`labs/02-loc-metrics/`](labs/02-loc-metrics/) | ПР2: метрика LOC на прикладі Shopizer, економіка за COCOMO, рівні мов C# і Java (звіт, презентація, скрипти вимірювання) |
| [`labs/03-function-points/`](labs/03-function-points/) | ПР3: функціональні точки Shopizer (306 транзакцій, 26 ILF, AFP 1 520), економіка (звіт, презентація, скрипти підрахунку) |
| [`labs/04-additional-points/`](labs/04-additional-points/) | ПР4: Feature, Object і Use-case points для Shopizer, порівняння з FP (звіт, презентація, скрипти) |
| [`labs/05-analogy/`](labs/05-analogy/) | ПР5: оцінка за аналогами на 20 open source проєктах, Euclid і Manhattan, калібрування (звіт, презентація, скрипти збору) |
| [`labs/06-cocomo/`](labs/06-cocomo/) | ПР6: COCOMO базова, проміжна і COCOMO II для Shopizer (звіт, презентація, розрахунки) |
| [`labs/07-scrum/`](labs/07-scrum/) | ПР7: Planning Poker для Product Backlog Shopizer, швидкість, вартість, план релізу (голосування змодельовано; звіт, презентація, скрипти) |

## Вимоги і порядок запуску

- Інструменти: `just`, `uv`, `git`, `cloc` 2.10, `pandoc`, Python 3, Node 18+, Google Chrome (для презентацій), Microsoft Word на macOS (експорт звіту в PDF).
- Скіли `kpi-lab-report` і `kpi-html-deck` у `~/.claude/skills/` (збірка звітів і презентацій).
- Спочатку виконати `just clone` у `labs/02-loc-metrics/`: ПР3 і ПР5 читають клон Shopizer з `labs/02-loc-metrics/data/src/` (у git не потрапляє).
- Далі в кожній лабі: `just data`, `just cite`, `just report`, `just deck`. Порядок за залежностями див. `docs/labs/dependencies.md` (ПР2, потім ПР3 і ПР6, потім ПР4 і ПР7, потім ПР5).
- `labs/05-analogy/` додатково клонує 30 репозиторіїв (близько 1 ГБ у `data/src/analogs`, ігнорується).
