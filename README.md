# БулгарМетрикс — модулна структура

Старт: `pip install -r requirements.txt` и `streamlit run app.py`.

- `app.py`: общ интерфейс и dropdown.
- `core/registry.py`: автоматично откриване по `config.toml`; зарежда само избрания анализ.
- `analyses/analysis_001/main.py`: оригиналният Анализ 01, преместен без промяна на изчисленията.
- `analyses/analysis_002/`: примерен модул в разработка.
- `shared/data_loader.py`: общи зареждания и помощни функции.
- `shared/theme.py`: оригинален CSS и шрифт.
- `data/`: оригиналните файлове с данни, без промяна.

Нов анализ: създайте `analyses/analysis_003/` с `__init__.py`, `config.toml` и `main.py` с функция `render()`. Регистърът автоматично ще го включи при следващо стартиране. `status` може да е `active`, `development` или `archived`; `visible=false` скрива анализа.

При по-нататъшно развитие може да се отделят `calculations.py` и `charts.py` от `analysis_001/main.py`. Тази първа миграция умишлено не променя изчислителната логика.

## Етап 3 — вътрешно разделяне на Анализ 01

- `analyses/analysis_001/ui.py` — Streamlit контролите, визуалното подреждане и описанията.
- `analyses/analysis_001/calculations.py` — 30-годишни проекции, натрупани разходи и текстови стойности.
- `analyses/analysis_001/tables.py` — статистически таблици, COICOP йерархия и оцветяване на избрани редове.
- `analyses/analysis_001/charts.py` — подготовка на историческите данни за графика и таблица.
- `analyses/analysis_001/scenarios.py` — конфигурация на сценариите.

Тестове: `python -m pytest -q` (след инсталиране на `requirements.txt` и `pytest`).
В средата за разработка са проверени 7 чисти теста чрез изолирана подмяна на зареждащия модул; пълно стартиране на Streamlit не е проверено.
