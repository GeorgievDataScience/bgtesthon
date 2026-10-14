from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "analyses" / "analysis_001"

def test_component_and_entrypoint_exist():
    assert (BASE / "components" / "context.py").exists()
    assert (BASE / "main.py").exists()

def test_ui_uses_context():
    source = (BASE / "ui.py").read_text(encoding="utf-8")
    assert "context = load_context()" in source
    assert "def render():" in source

def test_context_exports_expected_fields():
    tree = ast.parse((BASE / "components" / "context.py").read_text(encoding="utf-8"))
    names = {n.name for n in tree.body if isinstance(n, (ast.FunctionDef, ast.ClassDef))}
    assert {"AnalysisContext", "load_context", "flag_emoji"} <= names
