import pytest

from src.table_modifier.format.protocol import FormatProtocol


class DummyFormat(FormatProtocol):
    # Intentionally do not implement methods to hit NotImplementedError in protocol
    pass


def test_protocol_methods_raise_not_implemented():
    d = DummyFormat()
    with pytest.raises(NotImplementedError):
        d.components()
    with pytest.raises(NotImplementedError):
        d.header()
    with pytest.raises(NotImplementedError):
        d.footer()
    with pytest.raises(NotImplementedError):
        d.file_interface()
    with pytest.raises(NotImplementedError):
        d.metadata()

