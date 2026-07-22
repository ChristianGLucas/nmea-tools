from gen.messages_pb2 import NmeaSentence, EncodeOutput
from nodes.encode_sentence import encode_sentence
from nodes.parse_gga import parse_gga
from nodes.parse_rmc import parse_rmc
from gen.messages_pb2 import SentenceInput
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


def test_encode_sentence_gga_matches_hand_computed_oracle():
    # Independent oracle: for lat=10.5 (10 deg exactly 30.000' N) and
    # lon=-20.25 (20 deg exactly 15.000' W), the expected NMEA body was
    # hand-assembled field-by-field and its checksum hand-computed with a
    # standalone XOR script (not via this package or pynmea2):
    #   body = "GPGGA,010203,1030.00000,N,02015.00000,W,1,08,0.9,100.0,M,20.0,M,,"
    #   XOR(body) == 0x56
    msg = NmeaSentence(
        talker_id="GP", sentence_id="GGA",
        has_position=True, lat=10.5, lon=-20.25,
        has_time=True, utc_time="01:02:03.000",
        has_fix_quality=True, fix_quality=1,
        has_satellites=True, num_satellites=8, hdop=0.9,
        has_altitude=True, altitude_m=100.0, geoid_separation_m=20.0,
    )
    result = encode_sentence(_TestContext(), msg)
    assert isinstance(result, EncodeOutput)
    assert result.error == ""
    assert result.raw == "$GPGGA,010203,1030.00000,N,02015.00000,W,1,08,0.9,100.0,M,20.0,M,,*56"


def test_encode_sentence_rmc_matches_hand_computed_oracle():
    # Independent oracle, same method as above:
    #   body = "GPRMC,010203,A,1030.00000,N,02015.00000,W,5.0,90.0,010124,3.0,W"
    #   XOR(body) == 0x4B
    msg = NmeaSentence(
        talker_id="GP", sentence_id="RMC",
        has_position=True, lat=10.5, lon=-20.25,
        has_time=True, utc_time="01:02:03.000",
        has_date=True, date="2024-01-01",
        has_status=True, status="A",
        has_speed=True, speed_knots=5.0,
        has_course=True, course_true_deg=90.0,
        has_mag_variation=True, mag_variation_deg=-3.0,
    )
    result = encode_sentence(_TestContext(), msg)
    assert result.error == ""
    assert result.raw == "$GPRMC,010203,A,1030.00000,N,02015.00000,W,5.0,90.0,010124,3.0,W*4B"


def test_encode_sentence_round_trips_through_parse():
    # Self-consistency check (in addition to the hand-computed oracles
    # above): encoding a GGA fix then re-parsing it recovers equivalent
    # structured values (not byte-identical text — encode uses 5 decimal
    # places of minutes precision).
    msg = NmeaSentence(
        talker_id="GP", sentence_id="GGA",
        has_position=True, lat=48.1173, lon=11.516667,
        has_time=True, utc_time="12:35:19.000",
        has_fix_quality=True, fix_quality=1,
        has_satellites=True, num_satellites=8, hdop=0.9,
        has_altitude=True, altitude_m=545.4, geoid_separation_m=46.9,
    )
    encoded = encode_sentence(_TestContext(), msg)
    assert encoded.error == ""
    reparsed = parse_gga(_TestContext(), SentenceInput(sentence=encoded.raw))
    assert reparsed.error == ""
    assert reparsed.checksum_valid is True
    assert abs(reparsed.lat - 48.1173) < 1e-4
    assert abs(reparsed.lon - 11.516667) < 1e-4
    assert reparsed.fix_quality == 1
    assert reparsed.num_satellites == 8
    assert abs(reparsed.altitude_m - 545.4) < 1e-6


def test_encode_sentence_missing_talker_id():
    msg = NmeaSentence(sentence_id="GGA", has_position=True, lat=1.0, lon=1.0, has_time=True, utc_time="01:02:03.000")
    result = encode_sentence(_TestContext(), msg)
    assert result.error == "MISSING_REQUIRED_FIELD"
    assert result.raw == ""


def test_encode_sentence_unsupported_type():
    msg = NmeaSentence(talker_id="GP", sentence_id="GSV")
    result = encode_sentence(_TestContext(), msg)
    assert result.error == "UNSUPPORTED_SENTENCE_TYPE"
    assert result.raw == ""


def test_encode_sentence_gga_missing_position_is_structured_error():
    msg = NmeaSentence(talker_id="GP", sentence_id="GGA", has_time=True, utc_time="01:02:03.000")
    result = encode_sentence(_TestContext(), msg)
    assert result.error == "MISSING_REQUIRED_FIELD"
