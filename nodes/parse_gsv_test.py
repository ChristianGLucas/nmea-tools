from gen.messages_pb2 import SentenceInput, NmeaSentence
from nodes.parse_gsv import parse_gsv
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


# Independent oracle: hand-verified checksum XOR("GPGSV,3,1,11,03,03,111,00,
# 04,15,270,00,06,01,010,00,13,06,292,00") == 0x74; four satellite records
# read directly off the comma-delimited fields.
GSV_ORACLE = "$GPGSV,3,1,11,03,03,111,00,04,15,270,00,06,01,010,00,13,06,292,00*74"


def test_parse_gsv_oracle():
    result = parse_gsv(_TestContext(), SentenceInput(sentence=GSV_ORACLE))
    assert isinstance(result, NmeaSentence)
    assert result.error == ""
    assert result.talker_id == "GP"
    assert result.sentence_id == "GSV"
    assert result.checksum_valid is True
    assert result.gsv_total_messages == 3
    assert result.gsv_message_number == 1
    assert result.gsv_satellites_in_view_total == 11
    assert len(result.satellites) == 4
    first = result.satellites[0]
    assert first.prn == 3
    assert first.elevation_deg == 3
    assert first.azimuth_deg == 111
    assert first.has_snr is True
    assert first.snr_db == 0
    prns = [s.prn for s in result.satellites]
    assert prns == [3, 4, 6, 13]


def test_parse_gsv_rejects_wrong_sentence_type():
    gsa = "$GPGSA,A,3,04,05,,09,12,,,24,,,,,2.5,1.3,2.1*39"
    result = parse_gsv(_TestContext(), SentenceInput(sentence=gsa))
    assert result.error == "WRONG_SENTENCE_TYPE"
    assert result.sentence_id == "GSA"
