import pytest

from pathlib import Path

from src.table_modifier.config.state import FileList, State
from src.table_modifier.file_status import FileStatus


def test_filelist_basic_ops(tmp_path: Path):
    fl = FileList("tracked_files_test")
    p1 = tmp_path / "a.csv"
    p1.write_text("h1\n1\n")

    # append and contains
    fl.append(p1.as_posix(), FileStatus())
    assert len(fl) == 1
    assert p1.as_posix() in fl

    # getitem
    status = fl[p1.as_posix()]
    assert isinstance(status, FileStatus)

    # iteration
    items = list(iter(fl))
    assert len(items) == 1

    # delete and clear
    del fl[p1.as_posix()]
    assert len(fl) == 0
    fl.append(p1.as_posix(), FileStatus())
    fl.clear()
    assert len(fl) == 0


def test_state_controls_update_and_get():
    s = State()
    s.add_control("alpha", 1)
    assert s.controls["alpha"] == 1
    s.update_control("alpha", 2)
    assert s.controls["alpha"] == 2
    # dict-like set
    s["beta"] = 3
    assert s.controls["beta"] == 3

