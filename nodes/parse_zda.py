from gen.messages_pb2 import SentenceInput, NmeaSentence
from gen.axiom_context import AxiomContext
from nodes._nmea_helpers import parse_typed


def parse_zda(ax: AxiomContext, input: SentenceInput) -> NmeaSentence:
    """Parses a ZDA (Time and Date) sentence into UTC time, calendar date
    (unambiguous 4-digit year), and local time zone offset. Rejects a
    non-ZDA sentence with a structured WRONG_SENTENCE_TYPE error rather
    than silently parsing it.
    """
    return NmeaSentence(**parse_typed(input.sentence, "ZDA"))
