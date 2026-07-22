from gen.messages_pb2 import SentenceInput, NmeaSentence
from gen.axiom_context import AxiomContext
from nodes._nmea_helpers import parse_typed


def parse_gga(ax: AxiomContext, input: SentenceInput) -> NmeaSentence:
    """Parses a GGA (Global Positioning System Fix Data) sentence into
    position (lat/lon), UTC time, fix quality (invalid/GPS/DGPS/RTK/etc.),
    satellite count, HDOP, altitude, and geoid separation. Rejects a
    non-GGA sentence with a structured WRONG_SENTENCE_TYPE error rather
    than silently parsing it.
    """
    return NmeaSentence(**parse_typed(input.sentence, "GGA"))
