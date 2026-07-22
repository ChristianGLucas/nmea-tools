from gen.messages_pb2 import SentenceInput, NmeaSentence
from nodes.parse_gga import parse_gga
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


# Independent oracle: classic Wikipedia NMEA 0183 GGA example, checksum and
# lat/lon hand-verified from scratch (see parse_sentence_test.py).
GGA_ORACLE = "$GPGGA,123519,4807.038,N,01131.000,E,1,08,0.9,545.4,M,46.9,M,,*47"


def test_parse_gga_oracle():
    result = parse_gga(_TestContext(), SentenceInput(sentence=GGA_ORACLE))
    assert isinstance(result, NmeaSentence)
    assert result.error == ""
    assert result.talker_id == "GP"
    assert result.sentence_id == "GGA"
    assert result.checksum_valid is True
    assert result.has_position is True
    assert abs(result.lat - 48.1173) < 1e-4
    assert abs(result.lon - 11.516667) < 1e-4
    assert result.utc_time == "12:35:19.000"
    assert result.fix_quality == 1
    assert result.num_satellites == 8
    assert abs(result.hdop - 0.9) < 1e-9
    assert abs(result.altitude_m - 545.4) < 1e-9
    assert abs(result.geoid_separation_m - 46.9) < 1e-9


def test_parse_gga_no_fix_has_position_false_not_zero_confused_with_real():
    # gps_qual=0 (invalid fix): lat/lon fields are blank. has_position must
    # be false, not "0.0,0.0" (which would look like a real equator/prime-
    # meridian fix). Checksum independently hand-verified: 0x6B.
    no_fix = "$GPGGA,123519,,,,,0,00,,,M,,M,,*6B"
    result = parse_gga(_TestContext(), SentenceInput(sentence=no_fix))
    assert result.error == ""
    assert result.checksum_valid is True
    assert result.has_position is False
    assert result.has_fix_quality is True
    assert result.fix_quality == 0


def test_parse_gga_rejects_wrong_sentence_type():
    rmc = "$GPRMC,123519,A,4807.038,N,01131.000,E,022.4,084.4,230394,003.1,W*6A"
    result = parse_gga(_TestContext(), SentenceInput(sentence=rmc))
    assert result.error == "WRONG_SENTENCE_TYPE"
    assert result.sentence_id == "RMC"


def test_parse_gga_malformed_input_not_crashed():
    result = parse_gga(_TestContext(), SentenceInput(sentence="garbage, not nmea at all"))
    assert result.error in ("MALFORMED_SENTENCE", "UNSUPPORTED_SENTENCE_TYPE")
