from gen.messages_pb2 import SentenceInput, NmeaSentence
from nodes.parse_zda import parse_zda
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


# Independent oracle: hand-verified checksum XOR("GPZDA,201530.00,04,07,
# 2002,00,00") == 0x60.
ZDA_ORACLE = "$GPZDA,201530.00,04,07,2002,00,00*60"


def test_parse_zda_oracle():
    result = parse_zda(_TestContext(), SentenceInput(sentence=ZDA_ORACLE))
    assert isinstance(result, NmeaSentence)
    assert result.error == ""
    assert result.talker_id == "GP"
    assert result.sentence_id == "ZDA"
    assert result.checksum_valid is True
    assert result.utc_time == "20:15:30.000"
    assert result.has_date is True
    assert result.date == "2002-07-04"
    assert result.has_zone_offset is True
    assert result.zone_hours == 0
    assert result.zone_minutes == 0


def test_parse_zda_rejects_wrong_sentence_type():
    gsv = "$GPGSV,3,1,11,03,03,111,00,04,15,270,00,06,01,010,00,13,06,292,00*74"
    result = parse_zda(_TestContext(), SentenceInput(sentence=gsv))
    assert result.error == "WRONG_SENTENCE_TYPE"
    assert result.sentence_id == "GSV"
