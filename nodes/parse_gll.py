from gen.messages_pb2 import SentenceInput, NmeaSentence
from gen.axiom_context import AxiomContext
from nodes._nmea_helpers import parse_typed


def parse_gll(ax: AxiomContext, input: SentenceInput) -> NmeaSentence:
    """Parses a GLL (Geographic Position — Latitude/Longitude) sentence into
    position, UTC time, and active/void status. Rejects a non-GLL sentence
    with a structured WRONG_SENTENCE_TYPE error rather than silently
    parsing it.
    """
    return NmeaSentence(**parse_typed(input.sentence, "GLL"))
