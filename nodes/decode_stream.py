from gen.messages_pb2 import StreamInput, StreamOutput
from gen.axiom_context import AxiomContext
from nodes._nmea_helpers import decode_stream as _decode


def decode_stream(ax: AxiomContext, input: StreamInput) -> StreamOutput:
    """Decodes a multi-line block of NMEA 0183 sentences (e.g. a logged
    receiver session) into a normalized, ordered list of decoded
    NmeaSentence records — one per input line, each independently parsed
    and checksum-checked, so one malformed line never fails the whole
    batch.
    """
    return StreamOutput(**_decode(input.data))
