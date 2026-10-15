"""Pure function regression checks (requires normal project dependencies)."""
import pandas as pd
from analyses.analysis_001.calculations import build_projection_tables, build_totals_table
from analyses.analysis_001.tables import build_statistics_table, build_hierarchy_table
from analyses.analysis_001.charts import prepare_index_data


def test_projection_matches_original_formula():
    result = build_projection_tables(12000, 1.04)
    assert len(result.projected_values) == 31
    assert result.projected_values[0] == 12000
    assert result.projected_values[30] == 12000 * (1.04 ** 30)
    assert result.yearly_rounded[5] == round(12000 * 1.04**5)
    assert result.monthly_rounded[5] == round((12000 * 1.04**5) / 12)
    assert result.monthly_table.shape == (31, 1)
    assert list(result.monthly_table.columns) == ["Месечен разход"]
    assert result.yearly_table.iloc[5, 0] == (
        "След 5 г.\n"
        "ще бъде 💵14 600\n"
        "базата е 12 000\n"
        "натрупаната промяна е 💵2 600"
    )
    assert result.monthly_table.iloc[0, 0].startswith("Текущата година\nе 💵")


def test_totals_match_original_sum_and_rounding():
    result = build_projection_tables(12000, 1.04)
    totals = build_totals_table([1, 2, 30], result.projected_values, 12000)
    assert totals.shape == (3, 1)
    assert totals.iloc[0, 0] == (
        "За 1 година\n"
        "ще сте платили общо 💵12 000\n"
        "базата е 12 000\n"
        "натрупаната промяна е 💵0"
    )
    assert totals.iloc[1, 0].startswith("За 2 години\nще сте платили общо 💵")


def test_statistics_levels():
    rows, table = build_statistics_table(pd.Series([1.0, 2.0, 3.0, 4.0]))
    assert len(rows) == 8
    assert rows[3][0] == 2.5
    assert rows[4][0] == 2.5
    assert list(table.columns) == ['Процент', 'Статистика', 'Ниво', 'Сценарии']


def test_chart_data_sorting():
    df = pd.DataFrame({'year':[2024,2023], 'idx_value':[110,100], 'percentage_change_inx':[10,5]})
    chart, history = prepare_index_data(df)
    assert chart['year'].tolist() == [2023,2024]
    assert history['Година'].tolist() == [2023,2024]


def test_hierarchy():
    row = pd.Series({'division code':'01', 'division_name_bg':'Тест', 'group code':None,
        'group_name_bg':None, 'class code':None, 'class_name_bg':None,
        'subclass code':None, 'subclass_name_bg':None,
        'detailed level code':None, 'detailed_level_name_bg':None})
    styler = build_hierarchy_table(row,'01')
    assert styler.data.iloc[0,1] == '01 — Тест'
