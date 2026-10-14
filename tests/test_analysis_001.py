"""Regression checks for extracted pure calculation helpers."""
from analyses.analysis_001.calculations import change_sentence, projection_labels_for

def test_change_sentence():
    assert change_sentence("След 5 г.", 12000, 480) == (
        "След 5 г. базата е 12 000, а натрупаната промяна е 💵480."
    )
    assert change_sentence("След 5 г.", 12000, -480) == (
        "След 5 г. базата е 12 000, а натрупаната промяна е -💵480."
    )

def test_projection_labels():
    assert projection_labels_for("Месечният", [100, 105], [0, 1]) == [
        "Месечният ви разход за текущата година е 💵100.",
        "Месечният ви разход след 1 г. ще бъде 💵105.",
    ]
