from gen.messages_pb2 import SentenceInput, NmeaSentence
from gen.axiom_context import AxiomContext
from nodes._nmea_helpers import parse_typed


def parse_gsv(ax: AxiomContext, input: SentenceInput) -> NmeaSentence:
    """Parses a GSV (Satellites in View) sentence into its page number/
    total pages, the total satellite count, and up to four satellites'
    PRN, elevation, azimuth, and SNR (a full sky view requires combining
    several paged GSV sentences — DecodeStream does that combination
    across a stream). Rejects a non-GSV sentence with a structured
    WRONG_SENTENCE_TYPE error rather than silently parsing it.
    """
    return NmeaSentence(**parse_typed(input.sentence, "GSV"))
