from gen.messages_pb2 import SentenceInput, NmeaSentence
from nodes.parse_gsa import parse_gsa
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


# Independent oracle: hand-verified checksum XOR("GPGSA,A,3,04,05,,09,12,,,
# 24,,,,,2.5,1.3,2.1") == 0x39; active PRNs hand-counted from the non-empty
# SV-ID fields (04,05,09,12,24).
GSA_ORACLE = "$GPGSA,A,3,04,05,,09,12,,,24,,,,,2.5,1.3,2.1*39"


def test_parse_gsa_oracle():
    result = parse_gsa(_TestContext(), SentenceInput(sentence=GSA_ORACLE))
    assert isinstance(result, NmeaSentence)
    assert result.error == ""
    assert result.talker_id == "GP"
    assert result.sentence_id == "GSA"
    assert result.checksum_valid is True
    assert result.fix_selection_mode == "A"
    assert result.fix_dimension == "3"
    assert list(result.active_satellite_prns) == [4, 5, 9, 12, 24]
    assert abs(result.pdop - 2.5) < 1e-9
    assert abs(result.hdop - 1.3) < 1e-9
    assert abs(result.vdop - 2.1) < 1e-9


def test_parse_gsa_rejects_wrong_sentence_type():
    gll = "$GPGLL,4916.45,N,12311.12,W,225444,A*31"
    result = parse_gsa(_TestContext(), SentenceInput(sentence=gll))
    assert result.error == "WRONG_SENTENCE_TYPE"
    assert result.sentence_id == "GLL"
