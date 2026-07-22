from gen.messages_pb2 import SentenceInput, ChecksumResult
from nodes.validate_checksum import validate_checksum
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


# Independent oracle: XOR("GPGGA,123519,4807.038,N,01131.000,E,1,08,0.9,
# 545.4,M,46.9,M,,") hand-computed == 0x47 (matches the classic Wikipedia
# NMEA 0183 GGA example's published checksum), computed with a standalone
# script, not through pynmea2 or this package's own code.
GGA_ORACLE = "$GPGGA,123519,4807.038,N,01131.000,E,1,08,0.9,545.4,M,46.9,M,,*47"


def test_validate_checksum_valid():
    result = validate_checksum(_TestContext(), SentenceInput(sentence=GGA_ORACLE))
    assert isinstance(result, ChecksumResult)
    assert result.error == ""
    assert result.valid is True
    assert result.expected == "47"
    assert result.actual == "47"


def test_validate_checksum_mismatch_reports_both_bytes():
    result = validate_checksum(
        _TestContext(),
        SentenceInput(sentence="$GPGGA,123519,4807.038,N,01131.000,E,1,08,0.9,545.4,M,46.9,M,,*00"),
    )
    assert result.error == ""  # a checked-and-failed checksum is not itself an error
    assert result.valid is False
    assert result.expected == "47"
    assert result.actual == "00"


def test_validate_checksum_works_on_a_sentence_type_this_package_does_not_model():
    # Checksum validation is independent of sentence-type recognition — an
    # uncommon/unlisted talker sentence still gets a real checksum check.
    # Independently hand-verified: XOR("GPXYZ,1,2,3") == 0x50.
    result = validate_checksum(_TestContext(), SentenceInput(sentence="$GPXYZ,1,2,3*50"))
    assert result.valid is True
    assert result.error == ""


def test_validate_checksum_missing_checksum():
    result = validate_checksum(_TestContext(), SentenceInput(sentence="$GPGGA,123519,4807.038,N,01131.000,E,1,08,0.9,545.4,M,46.9,M,,"))
    assert result.valid is False
    assert result.error == "CHECKSUM_MISSING"
    assert result.expected == "47"


def test_validate_checksum_malformed_sentence_not_crashed():
    result = validate_checksum(_TestContext(), SentenceInput(sentence="not even close to nmea"))
    assert result.valid is False
    assert result.error == "MALFORMED_SENTENCE"


def test_validate_checksum_empty_input():
    result = validate_checksum(_TestContext(), SentenceInput(sentence=""))
    assert result.valid is False
    assert result.error == "MALFORMED_SENTENCE"
