from gen.messages_pb2 import SentenceInput, NmeaSentence
from nodes.parse_sentence import parse_sentence
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


# Independent oracle: the classic NMEA 0183 GGA example (Wikipedia's "NMEA
# 0183" article). Checksum 0x47 and lat/lon hand-verified from scratch with
# a standalone XOR + degrees/minutes-to-decimal script (not via pynmea2)
# before writing this fixture.
GGA_ORACLE = "$GPGGA,123519,4807.038,N,01131.000,E,1,08,0.9,545.4,M,46.9,M,,*47"


def test_parse_sentence_gga_full_structured_fields():
    ax = _TestContext()
    result = parse_sentence(ax, SentenceInput(sentence=GGA_ORACLE))
    assert isinstance(result, NmeaSentence)
    assert result.error == ""
    assert result.talker_id == "GP"
    assert result.sentence_id == "GGA"
    assert result.checksum_valid is True
    assert result.has_position is True
    assert abs(result.lat - 48.1173) < 1e-4
    assert abs(result.lon - 11.516667) < 1e-4
    assert result.has_time is True
    assert result.utc_time == "12:35:19.000"
    assert result.has_fix_quality is True
    assert result.fix_quality == 1
    assert result.has_satellites is True
    assert result.num_satellites == 8
    assert abs(result.hdop - 0.9) < 1e-9
    assert result.has_altitude is True
    assert abs(result.altitude_m - 545.4) < 1e-9
    assert abs(result.geoid_separation_m - 46.9) < 1e-9


def test_parse_sentence_generic_fallback_for_uncovered_type():
    # HDT (Heading, True) is one of pynmea2's ~70 talker types but not one
    # of this package's seven CORE_TYPES with full field extraction.
    # Checksum independently hand-verified: XOR("GPHDT,123.4,T") == 0x31.
    result = parse_sentence(_TestContext(), SentenceInput(sentence="$GPHDT,123.4,T*31"))
    assert result.error == ""
    assert result.talker_id == "GP"
    assert result.sentence_id == "HDT"
    assert result.checksum_valid is True
    assert result.has_position is False
    assert result.has_time is False


def test_parse_sentence_bad_checksum_is_structured_error_not_crash():
    result = parse_sentence(
        _TestContext(),
        SentenceInput(sentence="$GPGGA,123519,4807.038,N,01131.000,E,1,08,0.9,545.4,M,46.9,M,,*00"),
    )
    assert result.error == "CHECKSUM_MISMATCH"
    assert result.checksum_valid is False


def test_parse_sentence_unsupported_type_is_structured_error():
    result = parse_sentence(_TestContext(), SentenceInput(sentence="$GPXYZ,1,2,3*50"))
    assert result.error == "UNSUPPORTED_SENTENCE_TYPE"


def test_parse_sentence_empty_input():
    result = parse_sentence(_TestContext(), SentenceInput(sentence=""))
    assert result.error == "EMPTY_INPUT"


def test_parse_sentence_large_input_does_not_crash():
    huge = "$GPGGA," + ("1" * 2000) + "*00"
    result = parse_sentence(_TestContext(), SentenceInput(sentence=huge))
    # Not valid GGA content and a bad checksum, but must fail structured,
    # never raise.
    assert result.error != ""


def test_parse_sentence_is_deterministic():
    a = parse_sentence(_TestContext(), SentenceInput(sentence=GGA_ORACLE))
    b = parse_sentence(_TestContext(), SentenceInput(sentence=GGA_ORACLE))
    assert a == b
