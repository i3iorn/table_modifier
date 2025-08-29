import pytest

from pathlib import Path

import pytest

from src.table_modifier.file_interface.factory import FileInterfaceFactory, load, save
from src.table_modifier.file_interface.utils import from_file_path
from src.table_modifier.file_interface.protocol import FileInterfaceProtocol


class DummyInterface:
    file_type = "dummy"

    def __init__(self, file_path):
        from pathlib import Path as P
        self.path = P(str(file_path))
        self._data: list[dict] = []

    @property
    def name(self) -> str:
        return self.path.name

    @classmethod
    def can_handle(cls, file_path: str) -> bool:
        return str(file_path).endswith(".dummy")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):  # pragma: no cover - context mgmt trivial
        return False

    def append_df(self, df):  # pragma: no cover - not used in this test
        raise NotImplementedError

    def append_list(self, data):
        self._data.extend(list(data))

    @property
    def encoding(self) -> str:
        return "utf-8"

    def load(self):  # pragma: no cover - not used
        raise NotImplementedError

    def iter_load(self, chunksize: int = 1000):  # pragma: no cover - not used
        raise NotImplementedError

    def iter_columns(self, value_count=None, chunksize: int = 1000):  # pragma: no cover
        raise NotImplementedError

    def stream_rows(self):  # pragma: no cover - not used
        raise NotImplementedError

    def set_header_rows_to_skip(self, header_rows: int):  # pragma: no cover
        pass

    def save(self):  # pragma: no cover - not used
        pass

    def save_as(self, file_path: str):  # pragma: no cover - not used
        pass

    def get_schema(self):  # pragma: no cover - not used
        return {}

    def load_metadata(self):  # pragma: no cover - not used
        return {}

    def validate(self, df):  # pragma: no cover - not used
        pass

    def __reduce__(self):  # pragma: no cover - not used
        return (self.__class__, (self.path,))

    def __hash__(self):
        return hash(self.path)

    def __eq__(self, other):
        return isinstance(other, DummyInterface) and other.path == self.path


@pytest.fixture(autouse=True)
def ensure_dummy_registered():
    # Register dummy handler if not already present
    try:
        FileInterfaceFactory.register(DummyInterface)
    except Exception:
        pass
    yield


def test_factory_can_handle_and_create(tmp_path: Path):
    p = tmp_path / "test.dummy"
    p.write_text("")
    assert FileInterfaceFactory.can_handle(str(p))
    iface = FileInterfaceFactory.create(str(p))
    assert isinstance(iface, DummyInterface)
    assert iface.name == "test.dummy"


def test_from_file_path_roundtrip(tmp_path: Path):
    p = tmp_path / "x.dummy"
    p.write_text("")
    iface = from_file_path(str(p))
    assert isinstance(iface, DummyInterface)
    # Passing the interface returns itself
    same = from_file_path(iface)
    assert same is iface


def test_load_and_save_dispatch_to_handler(tmp_path: Path):
    p = tmp_path / "y.dummy"
    p.write_text("")
    iface = load(str(p))
    assert isinstance(iface, DummyInterface)
    # save should call append_list and then save() on the interface; our dummy doesn't write to disk
    save(iface, [{"a": 1}])
    assert iface._data == [{"a": 1}]

