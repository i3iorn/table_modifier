import pytest
from pathlib import Path
from click.testing import CliRunner
from src.table_modifier.cli import main


def test_cli_runs_and_writes_output(tmp_path: Path):
    # Prepare a simple CSV input
    inp = tmp_path / "in.csv"
    inp.write_text("a,b\n1,2\n", encoding="utf-8")
    outp = tmp_path / "out.csv"

    runner = CliRunner()
    result = runner.invoke(main, ["-l", "en", inp.as_posix(), outp.as_posix()])
    assert result.exit_code == 0, result.output
    assert outp.exists()
    # content should be a CSV header present
    text = outp.read_text(encoding="utf-8")
    assert text.startswith("a,b")

