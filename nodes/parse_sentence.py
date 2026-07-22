from gen.messages_pb2 import SentenceInput, NmeaSentence
from gen.axiom_context import AxiomContext
from nodes._nmea_helpers import parse_any


def parse_sentence(ax: AxiomContext, input: SentenceInput) -> NmeaSentence:
    """Parses a single raw NMEA 0183 sentence of any of the ~70 standard
    talker sentence types, auto-detecting talker ID and sentence type and
    validating its checksum. GGA, RMC, GLL, VTG, GSA, GSV, and ZDA get every
    applicable structured field populated; any other recognized sentence
    type returns talker_id/sentence_id/raw/checksum_valid with structured
    fields left at their zero value. Malformed input or an unrecognized
    sentence type returns a structured error, never a crash.
    """
    return NmeaSentence(**parse_any(input.sentence))
