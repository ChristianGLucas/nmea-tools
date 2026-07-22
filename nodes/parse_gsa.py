from gen.messages_pb2 import SentenceInput, NmeaSentence
from gen.axiom_context import AxiomContext
from nodes._nmea_helpers import parse_typed


def parse_gsa(ax: AxiomContext, input: SentenceInput) -> NmeaSentence:
    """Parses a GSA (GNSS DOP and Active Satellites) sentence into fix
    dimension (no-fix/2D/3D), automatic-vs-manual selection mode, the list
    of active satellite PRNs, and PDOP/HDOP/VDOP. Rejects a non-GSA
    sentence with a structured WRONG_SENTENCE_TYPE error rather than
    silently parsing it.
    """
    return NmeaSentence(**parse_typed(input.sentence, "GSA"))
