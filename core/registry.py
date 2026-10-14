"""File-based discovery of independent analysis packages."""
from dataclasses import dataclass
from importlib import import_module
from pathlib import Path
import re
import tomllib

ANALYSES_DIR = Path(__file__).resolve().parents[1] / "analyses"
VALID_STATUSES = {"active", "development", "archived"}

@dataclass(frozen=True)
class Analysis:
    id: str
    title: str
    order: int
    status: str
    visible: bool
    package: str

    @property
    def label(self) -> str:
        return f"Анализ {self.id}"

def discover_analyses() -> list[Analysis]:
    results = []
    seen = set()
    for folder in sorted(ANALYSES_DIR.glob("analysis_*")):
        config_file = folder / "config.toml"
        if not folder.is_dir() or not config_file.is_file():
            continue
        with config_file.open("rb") as handle:
            config = tomllib.load(handle)
        analysis_id = config["id"]
        if not isinstance(analysis_id, str) or not re.fullmatch(r"\d{3,}", analysis_id):
            raise ValueError(f"Invalid analysis id in {config_file}")
        if folder.name != f"analysis_{analysis_id}":
            raise ValueError(f"Folder and ID mismatch: {folder}")
        if analysis_id in seen:
            raise ValueError(f"Duplicate analysis ID: {analysis_id}")
        seen.add(analysis_id)
        status = config["status"]
        if status not in VALID_STATUSES:
            raise ValueError(f"Invalid status for {analysis_id}: {status}")
        if not isinstance(config["title"], str) or not config["title"].strip():
            raise ValueError(f"Missing title for {analysis_id}")
        if type(config["order"]) is not int or type(config["visible"]) is not bool:
            raise ValueError(f"Invalid order or visibility for {analysis_id}")
        if config["visible"]:
            results.append(Analysis(analysis_id, config["title"], config["order"], status, config["visible"], f"analyses.{folder.name}.main"))
    return sorted(results, key=lambda a: (a.order, a.id))

def load_analysis(analysis: Analysis):
    module = import_module(analysis.package)
    render = getattr(module, "render", None)
    if not callable(render):
        raise TypeError(f"{analysis.package} must expose render()")
    return render
