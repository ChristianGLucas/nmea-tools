from gen.messages_pb2 import SentenceInput, NmeaSentence
from gen.axiom_context import AxiomContext
from nodes._nmea_helpers import parse_typed


def parse_rmc(ax: AxiomContext, input: SentenceInput) -> NmeaSentence:
    """Parses an RMC (Recommended Minimum Specific GNSS Data) sentence into
    position, UTC date+time, active/void status, speed over ground (knots),
    true course, and magnetic variation (signed, +E/-W). Rejects a non-RMC
    sentence with a structured WRONG_SENTENCE_TYPE error rather than
    silently parsing it.
    """
    return NmeaSentence(**parse_typed(input.sentence, "RMC"))
