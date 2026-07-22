from gen.messages_pb2 import SentenceInput, NmeaSentence
from nodes.parse_rmc import parse_rmc
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


# Independent oracle: classic Wikipedia NMEA 0183 RMC example. Checksum
# (0x6A), lat/lon, and the signed magnetic variation (003.1,W -> -3.1) were
# hand-verified from scratch before writing this fixture.
RMC_ORACLE = "$GPRMC,123519,A,4807.038,N,01131.000,E,022.4,084.4,230394,003.1,W*6A"


def test_parse_rmc_oracle():
    result = parse_rmc(_TestContext(), SentenceInput(sentence=RMC_ORACLE))
    assert isinstance(result, NmeaSentence)
    assert result.error == ""
    assert result.talker_id == "GP"
    assert result.sentence_id == "RMC"
    assert result.checksum_valid is True
    assert result.has_position is True
    assert abs(result.lat - 48.1173) < 1e-4
    assert abs(result.lon - 11.516667) < 1e-4
    assert result.utc_time == "12:35:19.000"
    assert result.has_date is True
    assert result.date == "1994-03-23"
    assert result.status == "A"
    assert abs(result.speed_knots - 22.4) < 1e-9
    assert abs(result.course_true_deg - 84.4) < 1e-9
    assert result.has_mag_variation is True
    assert abs(result.mag_variation_deg - (-3.1)) < 1e-9  # 003.1,W -> signed negative


def test_parse_rmc_void_status_still_parses_fields():
    # status "V" (void) means the fix is not to be trusted, but the node
    # still reports what the receiver sent rather than hiding it.
    void = "$GPRMC,123519,V,4807.038,N,01131.000,E,022.4,084.4,230394,003.1,W*7D"
    result = parse_rmc(_TestContext(), SentenceInput(sentence=void))
    assert result.error == ""
    assert result.status == "V"


def test_parse_rmc_rejects_wrong_sentence_type():
    gga = "$GPGGA,123519,4807.038,N,01131.000,E,1,08,0.9,545.4,M,46.9,M,,*47"
    result = parse_rmc(_TestContext(), SentenceInput(sentence=gga))
    assert result.error == "WRONG_SENTENCE_TYPE"
    assert result.sentence_id == "GGA"
