from gen.messages_pb2 import SentenceInput, NmeaSentence
from gen.axiom_context import AxiomContext
from nodes._nmea_helpers import parse_typed


def parse_vtg(ax: AxiomContext, input: SentenceInput) -> NmeaSentence:
    """Parses a VTG (Track Made Good and Ground Speed) sentence into true
    and magnetic course, and speed over ground in both knots and km/h.
    Rejects a non-VTG sentence with a structured WRONG_SENTENCE_TYPE error
    rather than silently parsing it.
    """
    return NmeaSentence(**parse_typed(input.sentence, "VTG"))
