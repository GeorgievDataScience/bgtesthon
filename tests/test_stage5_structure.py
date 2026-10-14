from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parents[1]

def test_components_compile():
    for name in ("ui.py", "components/history.py", "components/description.py"):
        ast.parse((ROOT / "analyses/analysis_001" / name).read_text(encoding="utf-8"))

def test_render_functions():
    for name, fn in (("history.py", "render_history"), ("description.py", "render_description")):
        tree = ast.parse((ROOT / "analyses/analysis_001/components" / name).read_text(encoding="utf-8"))
        assert any(isinstance(n, ast.FunctionDef) and n.name == fn for n in tree.body)
