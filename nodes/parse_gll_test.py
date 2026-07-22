from gen.messages_pb2 import SentenceInput, NmeaSentence
from nodes.parse_gll import parse_gll
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


# Independent oracle: hand-verified checksum XOR("GPGLL,4916.45,N,12311.12,
# W,225444,A") == 0x31; lat/lon hand-converted from degrees/minutes.
GLL_ORACLE = "$GPGLL,4916.45,N,12311.12,W,225444,A*31"


def test_parse_gll_oracle():
    result = parse_gll(_TestContext(), SentenceInput(sentence=GLL_ORACLE))
    assert isinstance(result, NmeaSentence)
    assert result.error == ""
    assert result.talker_id == "GP"
    assert result.sentence_id == "GLL"
    assert result.checksum_valid is True
    assert result.has_position is True
    assert abs(result.lat - 49.274167) < 1e-4
    assert abs(result.lon - (-123.185333)) < 1e-4
    assert result.utc_time == "22:54:44.000"
    assert result.status == "A"


def test_parse_gll_rejects_wrong_sentence_type():
    vtg = "$GPVTG,054.7,T,034.4,M,005.5,N,010.2,K*48"
    result = parse_gll(_TestContext(), SentenceInput(sentence=vtg))
    assert result.error == "WRONG_SENTENCE_TYPE"
    assert result.sentence_id == "VTG"


def test_parse_gll_malformed_input_not_crashed():
    result = parse_gll(_TestContext(), SentenceInput(sentence="\x00\x01 not a sentence"))
    assert result.error in ("MALFORMED_SENTENCE", "UNSUPPORTED_SENTENCE_TYPE")
