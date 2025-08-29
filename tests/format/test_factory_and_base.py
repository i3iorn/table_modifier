import pytest
import json
from pathlib import Path

from src.table_modifier.format.factory import FormatFactory
from src.table_modifier.format.base import BaseFormat


def test_format_factory_creates_base_format(tmp_path: Path):
    config = {"components": ["a", "b"], "footer": "end"}
    p = tmp_path / "fmt.json"
    p.write_text(json.dumps(config), encoding="utf-8")

    fmt = FormatFactory().create_format(str(p))
    assert isinstance(fmt, BaseFormat)
    assert getattr(fmt, "components") == ["a", "b"]
    assert getattr(fmt, "footer") == "end"


def test_base_format_sets_attributes_directly():
    cfg = {"x": 1, "y": "z"}
    b = BaseFormat(cfg)
    assert b.x == 1
    assert b.y == "z"

