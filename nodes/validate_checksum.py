from gen.messages_pb2 import SentenceInput, ChecksumResult
from gen.axiom_context import AxiomContext
from nodes._nmea_helpers import check_checksum


def validate_checksum(ax: AxiomContext, input: SentenceInput) -> ChecksumResult:
    """Validates the trailing *HH checksum of a raw NMEA 0183 sentence
    against the XOR of its body, independent of whether the sentence type is
    one this package models — works for any well-formed "$...*HH" sentence,
    known type or not. Returns the expected and actual checksum bytes so a
    caller can see exactly why a mismatch occurred.
    """
    return ChecksumResult(**check_checksum((input.sentence or "").strip()))
