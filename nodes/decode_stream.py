from gen.messages_pb2 import StreamInput, StreamOutput
from gen.axiom_context import AxiomContext
from nodes._nmea_helpers import decode_stream as _decode


def decode_stream(ax: AxiomContext, input: StreamInput) -> StreamOutput:
    """Decodes a multi-line block of NMEA 0183 sentences (e.g. a logged
    receiver session) into a normalized, ordered list of decoded
    NmeaSentence records — one per input line, each independently parsed
    and checksum-checked, so one malformed line never fails the whole
    batch. Capped at 512 sentences / 256 KiB to stay well under the
    platform's request-size limit; oversized input is truncated
    (truncated=true) rather than rejected outright.
    """
    return StreamOutput(**_decode(input.data))
