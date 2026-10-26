"""SVG table for a category's place in the classification."""
import re

import pandas as pd

from shared.hierarchy_place import hierarchy_rows, hierarchy_svg


def _row(**values):
    base = {
        "division code": "CP01",
        "division_name_bg": "Храни и безалкохолни напитки",
        "group code": "CP011",
        "group_name_bg": "Храни",
        "class code": "CP0112",
        "class_name_bg": "Месо",
        "subclass code": None,
        "subclass_name_bg": None,
        "detailed level code": None,
        "detailed_level_name_bg": None,
    }
    base.update(values)
    return pd.Series(base)


def test_hierarchy_place_is_one_svg_and_marks_the_chosen_level():
    svg = hierarchy_svg(hierarchy_rows(_row(), "CP011"))
    assert svg.count("<svg ") == 1
    assert "Йерархично ниво" in svg
    assert "Код и наименование" in svg
    assert "🌐 Дивизия:" in svg
    assert "Детайлно ниво:" in svg
    assert "CP011 — Храни" in svg
    assert "Няма" in svg
    assert svg.count('class="selected"') == 1
    assert "#d9f2d9" in svg
    assert "#0b3d1e" in svg


def test_a_long_name_wraps_instead_of_staying_on_one_line():
    long_name = (
        "Карантии, кръв и други части от заклани животни, пресни, "
        "охладени или замразени, сушени, осолени, в саламура или пушени"
    )
    svg = hierarchy_svg(hierarchy_rows(_row(**{
        "subclass code": "CP01124",
        "subclass_name_bg": long_name,
    }), "CP01124"))
    name_lines = re.findall(r'<text class="name[^"]*"[^>]*>([^<]*)</text>', svg)
    assert long_name not in name_lines
    assert any("Карантии" in line for line in name_lines)
    assert any("пушени" in line for line in name_lines)
    assert len(name_lines) >= 6
    assert svg.count('class="selected"') == 1


def test_dark_theme_marks_the_svg():
    svg = hierarchy_svg(hierarchy_rows(_row(), "CP01"), theme="dark")
    assert 'class="theme-dark"' in svg
