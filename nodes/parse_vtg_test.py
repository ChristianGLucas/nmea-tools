from gen.messages_pb2 import SentenceInput, NmeaSentence
from nodes.parse_vtg import parse_vtg
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


# Independent oracle: hand-verified checksum XOR("GPVTG,054.7,T,034.4,M,
# 005.5,N,010.2,K") == 0x48.
VTG_ORACLE = "$GPVTG,054.7,T,034.4,M,005.5,N,010.2,K*48"


def test_parse_vtg_oracle():
    result = parse_vtg(_TestContext(), SentenceInput(sentence=VTG_ORACLE))
    assert isinstance(result, NmeaSentence)
    assert result.error == ""
    assert result.talker_id == "GP"
    assert result.sentence_id == "VTG"
    assert result.checksum_valid is True
    assert result.has_course is True
    assert abs(result.course_true_deg - 54.7) < 1e-9
    assert abs(result.course_magnetic_deg - 34.4) < 1e-9
    assert result.has_speed is True
    assert abs(result.speed_knots - 5.5) < 1e-9
    assert abs(result.speed_kmh - 10.2) < 1e-9


def test_parse_vtg_rejects_wrong_sentence_type():
    zda = "$GPZDA,201530.00,04,07,2002,00,00*60"
    result = parse_vtg(_TestContext(), SentenceInput(sentence=zda))
    assert result.error == "WRONG_SENTENCE_TYPE"
    assert result.sentence_id == "ZDA"


def test_parse_vtg_malformed_input_not_crashed():
    result = parse_vtg(_TestContext(), SentenceInput(sentence="###garbage###"))
    assert result.error in ("MALFORMED_SENTENCE", "UNSUPPORTED_SENTENCE_TYPE")
