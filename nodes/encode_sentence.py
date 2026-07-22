from gen.messages_pb2 import NmeaSentence, EncodeOutput
from gen.axiom_context import AxiomContext
from nodes._nmea_helpers import encode_sentence as _encode


def encode_sentence(ax: AxiomContext, input: NmeaSentence) -> EncodeOutput:
    """Encodes a structured NmeaSentence back into a well-formed, checksummed
    NMEA 0183 sentence string ("$..*HH"), for the GGA, RMC, GLL, VTG, GSA,
    and ZDA sentence types (selected by the talker_id/sentence_id fields).
    Returns a structured error if sentence_id is unsupported or a field the
    template requires is missing.
    """
    return EncodeOutput(**_encode(input))
