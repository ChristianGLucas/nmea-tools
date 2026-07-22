from gen.messages_pb2 import StreamInput, StreamOutput
from nodes.decode_stream import decode_stream
from gen.axiom_context import SecretStatus


class _TestContext:
    class _Logger:
        def debug(self, msg: str, **attrs) -> None: pass
        def info(self, msg: str, **attrs) -> None: pass
        def warn(self, msg: str, **attrs) -> None: pass
        def error(self, msg: str, **attrs) -> None: pass

    class _Secrets:
        def __init__(self, m: dict, revoked: set) -> None:
            self._m = m or {}
            self._revoked = revoked or set()
        def get(self, name: str):
            v = self._m.get(name)
            return (v, True) if v is not None else ("", False)
        def status(self, name: str) -> SecretStatus:
            if name in self._m:
                return SecretStatus.AVAILABLE
            if name in self._revoked:
                return SecretStatus.REVOKED
            return SecretStatus.UNSET

    def __init__(self, secrets_map: dict | None = None, revoked_names: set | None = None) -> None:
        self.log = self._Logger()
        self.secrets = self._Secrets(secrets_map or {}, revoked_names)
        self.execution_id = "test-execution-id"
        self.flow_id = "test-flow-id"
        self.tenant_id = "test-tenant-id"


# Independent oracle: the two classic Wikipedia NMEA 0183 examples (GGA
# checksum 0x47, RMC checksum 0x6A — both hand-verified from scratch), plus
# one deliberately malformed line to prove one bad line doesn't fail the
# batch.
GGA = "$GPGGA,123519,4807.038,N,01131.000,E,1,08,0.9,545.4,M,46.9,M,,*47"
RMC = "$GPRMC,123519,A,4807.038,N,01131.000,E,022.4,084.4,230394,003.1,W*6A"


def test_decode_stream_normalizes_a_mixed_realistic_session():
    data = "\n".join([GGA, RMC, "this line is garbage, not nmea", ""])
    result = decode_stream(_TestContext(), StreamInput(data=data))
    assert isinstance(result, StreamOutput)
    assert result.truncated is False
    assert len(result.sentences) == 3
    assert result.sentences[0].sentence_id == "GGA"
    assert result.sentences[0].error == ""
    assert abs(result.sentences[0].lat - 48.1173) < 1e-4
    assert result.sentences[1].sentence_id == "RMC"
    assert result.sentences[1].error == ""
    assert result.sentences[2].error != ""  # the garbage line, isolated
    assert result.valid_count == 2
    assert result.error_count == 1


def test_decode_stream_empty_input():
    result = decode_stream(_TestContext(), StreamInput(data=""))
    assert list(result.sentences) == []
    assert result.valid_count == 0
    assert result.error_count == 0
    assert result.truncated is False


def test_decode_stream_caps_line_count_and_marks_truncated():
    data = "\n".join([GGA] * 600)  # over the 512-line cap
    result = decode_stream(_TestContext(), StreamInput(data=data))
    assert result.truncated is True
    assert len(result.sentences) == 512
    assert result.valid_count == 512


def test_decode_stream_is_deterministic():
    data = "\n".join([GGA, RMC])
    a = decode_stream(_TestContext(), StreamInput(data=data))
    b = decode_stream(_TestContext(), StreamInput(data=data))
    assert a == b
