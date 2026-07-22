# Shared helpers for christiangeorgelucas/nmea-tools nodes.
#
# All parsing/encoding logic lives here as functions returning plain kwargs
# dicts; each node constructs its own typed protobuf output from the dict
# (`NmeaSentence(**helper(...))`) rather than this module importing the
# generated message classes and building them itself — keeps this module
# framework-agnostic and easy to unit test directly.
import datetime
import decimal

import pynmea2
from pynmea2.nmea import TalkerSentence

MAX_SENTENCE_LEN = 1024          # real NMEA 0183 sentences are <=82 bytes
MAX_STREAM_BYTES = 256 * 1024
MAX_STREAM_LINES = 512

CORE_TYPES = ("GGA", "RMC", "GLL", "VTG", "GSA", "GSV", "ZDA")
ENCODABLE_TYPES = ("GGA", "RMC", "GLL", "VTG", "GSA", "ZDA")


# ---------------------------------------------------------------- utilities

def _numf(v):
    """Best-effort float conversion; None on empty/unparseable, never raises."""
    if v is None:
        return None
    if isinstance(v, (int, float, decimal.Decimal)):
        return float(v)
    if isinstance(v, str):
        v = v.strip()
        if not v:
            return None
        try:
            return float(v)
        except ValueError:
            return None
    return None


def _numi(v):
    if isinstance(v, int) and not isinstance(v, bool):
        return v
    f = _numf(v)
    return int(f) if f is not None else None


def _as_time(v):
    return v if isinstance(v, datetime.time) else None


def _as_date(v):
    return v if isinstance(v, datetime.date) else None


def _fmt_time(t):
    t = _as_time(t)
    if t is None:
        return ""
    return t.strftime("%H:%M:%S.%f")[:-3]


def _fmt_date(d):
    d = _as_date(d)
    if d is None:
        return ""
    return d.strftime("%Y-%m-%d")


def _safe_latlon(obj):
    """(has_position, lat, lon) — tolerates missing/blank/malformed coordinates."""
    lat_raw = (getattr(obj, "lat", None) or "").strip()
    lon_raw = (getattr(obj, "lon", None) or "").strip()
    if not lat_raw or not lon_raw:
        return False, 0.0, 0.0
    try:
        return True, float(obj.latitude), float(obj.longitude)
    except (ValueError, TypeError, AttributeError):
        return False, 0.0, 0.0


# ------------------------------------------------------------- checksum


def check_checksum(raw: str) -> dict:
    """Validates the *HH checksum of a raw sentence, independent of whether
    the sentence type is one this package models in structured detail."""
    if not raw:
        return dict(valid=False, expected="", actual="", error="MALFORMED_SENTENCE")
    match = pynmea2.NMEASentence.sentence_re.match(raw)
    if not match:
        return dict(valid=False, expected="", actual="", error="MALFORMED_SENTENCE")
    nmea_str = match.group("nmea_str")
    checksum = match.group("checksum")
    expected = "%02X" % pynmea2.NMEASentence.checksum(nmea_str)
    if not checksum:
        return dict(valid=False, expected=expected, actual="", error="CHECKSUM_MISSING")
    actual = checksum.upper()
    return dict(valid=(actual == expected), expected=expected, actual=actual, error="")


# ------------------------------------------------------------- per-type extraction

def _extract_gga(obj):
    has_pos, lat, lon = _safe_latlon(obj)
    ts = _as_time(obj.timestamp)
    gps_qual = _numi(obj.gps_qual)
    num_sats = _numi(obj.num_sats)
    hdop = _numf(obj.horizontal_dil)
    alt = _numf(obj.altitude)
    geo_sep = _numf(obj.geo_sep)
    return dict(
        has_position=has_pos, lat=lat, lon=lon,
        has_time=ts is not None, utc_time=_fmt_time(ts),
        has_fix_quality=gps_qual is not None, fix_quality=gps_qual or 0,
        has_satellites=(num_sats is not None or hdop is not None),
        num_satellites=num_sats or 0, hdop=hdop or 0.0,
        has_altitude=alt is not None, altitude_m=alt or 0.0,
        geoid_separation_m=geo_sep or 0.0,
    )


def _extract_rmc(obj):
    has_pos, lat, lon = _safe_latlon(obj)
    ts = _as_time(obj.timestamp)
    ds = _as_date(obj.datestamp)
    status = (obj.status or "").strip()
    spd = _numf(obj.spd_over_grnd)
    course = _numf(obj.true_course)
    mag_var_raw = (obj.mag_variation or "").strip()
    mag_dir = (obj.mag_var_dir or "").strip()
    has_mag = False
    mag_deg = 0.0
    mv = _numf(mag_var_raw)
    if mv is not None:
        has_mag = True
        mag_deg = -mv if mag_dir == "W" else mv
    return dict(
        has_position=has_pos, lat=lat, lon=lon,
        has_time=ts is not None, utc_time=_fmt_time(ts),
        has_date=ds is not None, date=_fmt_date(ds),
        has_status=bool(status), status=status,
        has_speed=spd is not None, speed_knots=spd or 0.0,
        has_course=course is not None, course_true_deg=course or 0.0,
        has_mag_variation=has_mag, mag_variation_deg=mag_deg,
    )


def _extract_gll(obj):
    has_pos, lat, lon = _safe_latlon(obj)
    ts = _as_time(obj.timestamp)
    status = (obj.status or "").strip()
    return dict(
        has_position=has_pos, lat=lat, lon=lon,
        has_time=ts is not None, utc_time=_fmt_time(ts),
        has_status=bool(status), status=status,
    )


def _extract_vtg(obj):
    true_track = _numf(obj.true_track)
    mag_track = _numf(obj.mag_track)
    spd_kts = _numf(obj.spd_over_grnd_kts)
    spd_kmh = _numf(obj.spd_over_grnd_kmph)
    return dict(
        has_course=(true_track is not None or mag_track is not None),
        course_true_deg=true_track or 0.0,
        course_magnetic_deg=mag_track or 0.0,
        has_speed=(spd_kts is not None or spd_kmh is not None),
        speed_knots=spd_kts or 0.0, speed_kmh=spd_kmh or 0.0,
    )


def _extract_gsa(obj):
    prns = []
    for i in range(1, 13):
        v = _numi(getattr(obj, "sv_id%02d" % i, None))
        if v is not None:
            prns.append(v)
    mode = (obj.mode or "").strip()
    mode_fix = (obj.mode_fix_type or "").strip()
    pdop, hdop, vdop = _numf(obj.pdop), _numf(obj.hdop), _numf(obj.vdop)
    return dict(
        has_satellites=True,
        fix_selection_mode=mode, fix_dimension=mode_fix,
        pdop=pdop or 0.0, hdop=hdop or 0.0, vdop=vdop or 0.0,
        active_satellite_prns=prns,
    )


def _extract_gsv(obj):
    sats = []
    for i in range(1, 5):
        prn = _numi(getattr(obj, "sv_prn_num_%d" % i, None))
        if prn is None:
            continue
        elev = _numi(getattr(obj, "elevation_deg_%d" % i, None))
        azi = _numi(getattr(obj, "azimuth_%d" % i, None))
        snr = _numi(getattr(obj, "snr_%d" % i, None))
        sats.append(dict(
            prn=prn, elevation_deg=elev or 0, azimuth_deg=azi or 0,
            has_snr=snr is not None, snr_db=snr or 0,
        ))
    return dict(
        has_gsv=True,
        gsv_total_messages=_numi(obj.num_messages) or 0,
        gsv_message_number=_numi(obj.msg_num) or 0,
        gsv_satellites_in_view_total=_numi(obj.num_sv_in_view) or 0,
        satellites=sats,
    )


def _extract_zda(obj):
    ts = _as_time(obj.timestamp)
    day, month, year = _numi(obj.day), _numi(obj.month), _numi(obj.year)
    has_date = day is not None and month is not None and year is not None
    zh, zm = _numi(obj.local_zone), _numi(obj.local_zone_minutes)
    return dict(
        has_time=ts is not None, utc_time=_fmt_time(ts),
        has_date=has_date,
        date=("%04d-%02d-%02d" % (year, month, day)) if has_date else "",
        has_zone_offset=(zh is not None), zone_hours=zh or 0, zone_minutes=zm or 0,
    )


_EXTRACTORS = {
    "GGA": _extract_gga, "RMC": _extract_rmc, "GLL": _extract_gll,
    "VTG": _extract_vtg, "GSA": _extract_gsa, "GSV": _extract_gsv,
    "ZDA": _extract_zda,
}


# ------------------------------------------------------------- parse entry points

def _parse_core(raw: str):
    """Returns (kwargs_dict, obj_or_None). kwargs_dict always has talker_id/
    sentence_id/raw/checksum_valid/error set; obj is the pynmea2 object on
    success (for type-specific extraction), None on any failure."""
    raw = (raw or "").strip()
    if not raw:
        return dict(error="EMPTY_INPUT"), None
    if len(raw) > MAX_SENTENCE_LEN:
        return dict(error="INPUT_TOO_LONG"), None

    checksum = check_checksum(raw)

    try:
        obj = pynmea2.parse(raw, check=False)
    except pynmea2.ChecksumError:
        return dict(raw=raw, checksum_valid=False, error="CHECKSUM_MISMATCH"), None
    except pynmea2.SentenceTypeError:
        return dict(raw=raw, checksum_valid=checksum["valid"], error="UNSUPPORTED_SENTENCE_TYPE"), None
    except (pynmea2.ParseError, ValueError):
        return dict(raw=raw, checksum_valid=checksum["valid"], error="MALFORMED_SENTENCE"), None

    if not isinstance(obj, TalkerSentence):
        # Query ("--Q,xxx") or proprietary ("P...") sentences parse but
        # aren't one of the ~70 standard talker types this package models.
        return dict(raw=raw, checksum_valid=checksum["valid"], error="UNSUPPORTED_SENTENCE_TYPE"), None

    base = dict(
        talker_id=obj.talker, sentence_id=obj.sentence_type,
        raw=raw, checksum_valid=checksum["valid"], error="",
    )
    return base, obj


def parse_any(raw: str) -> dict:
    """Generic entry point: parses any recognized talker sentence, populating
    full structured fields for the seven CORE_TYPES and leaving the rest at
    their zero value (but still identifying talker/sentence/checksum) for
    every other recognized sentence type."""
    base, obj = _parse_core(raw)
    if obj is None:
        return base
    extractor = _EXTRACTORS.get(base["sentence_id"])
    if extractor is not None:
        base.update(extractor(obj))
    return base


def parse_typed(raw: str, expected_type: str) -> dict:
    """Like parse_any, but requires the sentence to be exactly expected_type
    (a WRONG_SENTENCE_TYPE error otherwise) and always runs its extractor."""
    base, obj = _parse_core(raw)
    if obj is None:
        return base
    if base["sentence_id"] != expected_type:
        return dict(
            talker_id=base["talker_id"], sentence_id=base["sentence_id"],
            raw=base["raw"], checksum_valid=base["checksum_valid"],
            error="WRONG_SENTENCE_TYPE",
        )
    base.update(_EXTRACTORS[expected_type](obj))
    return base


# ------------------------------------------------------------- encode

def _fmt_num(v, decimals):
    return ("%." + str(decimals) + "f") % v


def encode_sentence(msg) -> dict:
    """msg is the NmeaSentence protobuf input. Builds a checksummed raw
    sentence for one of ENCODABLE_TYPES from the fields the type needs."""
    talker = (msg.talker_id or "").strip().upper()
    sentence_id = (msg.sentence_id or "").strip().upper()
    if not talker or len(talker) != 2:
        return dict(raw="", error="MISSING_REQUIRED_FIELD")
    if sentence_id not in ENCODABLE_TYPES:
        return dict(raw="", error="UNSUPPORTED_SENTENCE_TYPE" if sentence_id else "MISSING_REQUIRED_FIELD")

    def lat_field():
        if not msg.has_position:
            return "", ""
        d = abs(msg.lat)
        deg = int(d)
        minutes = (d - deg) * 60
        return "%02d%08.5f" % (deg, minutes), ("N" if msg.lat >= 0 else "S")

    def lon_field():
        if not msg.has_position:
            return "", ""
        d = abs(msg.lon)
        deg = int(d)
        minutes = (d - deg) * 60
        return "%03d%08.5f" % (deg, minutes), ("E" if msg.lon >= 0 else "W")

    lat_s, lat_dir = lat_field()
    lon_s, lon_dir = lon_field()
    time_s = (msg.utc_time or "").replace(":", "")[:6] if msg.has_time else ""

    try:
        if sentence_id == "GGA":
            if not msg.has_position or not msg.has_time:
                return dict(raw="", error="MISSING_REQUIRED_FIELD")
            fields = [
                time_s, lat_s, lat_dir, lon_s, lon_dir,
                str(msg.fix_quality) if msg.has_fix_quality else "0",
                "%02d" % msg.num_satellites if msg.has_satellites else "",
                _fmt_num(msg.hdop, 1) if msg.has_satellites else "",
                _fmt_num(msg.altitude_m, 1) if msg.has_altitude else "", "M",
                _fmt_num(msg.geoid_separation_m, 1) if msg.has_altitude else "", "M",
                "", "",
            ]
        elif sentence_id == "RMC":
            if not msg.has_position or not msg.has_time:
                return dict(raw="", error="MISSING_REQUIRED_FIELD")
            date_s = msg.date.replace("-", "")[2:] if msg.has_date and len(msg.date) == 10 else ""
            date_s = (date_s[4:6] + date_s[2:4] + date_s[0:2]) if date_s else ""
            mag_s, mag_dir = "", ""
            if msg.has_mag_variation:
                mag_s = _fmt_num(abs(msg.mag_variation_deg), 1)
                mag_dir = "W" if msg.mag_variation_deg < 0 else "E"
            fields = [
                time_s, "A" if (msg.status or "A") == "A" else "V",
                lat_s, lat_dir, lon_s, lon_dir,
                _fmt_num(msg.speed_knots, 1) if msg.has_speed else "",
                _fmt_num(msg.course_true_deg, 1) if msg.has_course else "",
                date_s, mag_s, mag_dir,
            ]
        elif sentence_id == "GLL":
            if not msg.has_position:
                return dict(raw="", error="MISSING_REQUIRED_FIELD")
            fields = [
                lat_s, lat_dir, lon_s, lon_dir, time_s,
                "A" if (msg.status or "A") == "A" else "V",
            ]
        elif sentence_id == "VTG":
            fields = [
                _fmt_num(msg.course_true_deg, 1) if msg.has_course else "", "T",
                _fmt_num(msg.course_magnetic_deg, 1) if msg.has_course else "", "M",
                _fmt_num(msg.speed_knots, 1) if msg.has_speed else "", "N",
                _fmt_num(msg.speed_kmh, 1) if msg.has_speed else "", "K",
            ]
        elif sentence_id == "GSA":
            prns = list(msg.active_satellite_prns)[:12]
            prn_fields = ["%02d" % p for p in prns] + [""] * (12 - len(prns))
            fields = [
                msg.fix_selection_mode or "A", msg.fix_dimension or "1",
                *prn_fields,
                _fmt_num(msg.pdop, 1) if msg.has_satellites else "",
                _fmt_num(msg.hdop, 1) if msg.has_satellites else "",
                _fmt_num(msg.vdop, 1) if msg.has_satellites else "",
            ]
        elif sentence_id == "ZDA":
            if not msg.has_time or not msg.has_date or len(msg.date) != 10:
                return dict(raw="", error="MISSING_REQUIRED_FIELD")
            year, month, day = msg.date.split("-")
            fields = [
                time_s, day, month, year,
                "%02d" % msg.zone_hours if msg.has_zone_offset else "00",
                "%02d" % msg.zone_minutes if msg.has_zone_offset else "00",
            ]
        else:  # pragma: no cover - guarded above
            return dict(raw="", error="UNSUPPORTED_SENTENCE_TYPE")
    except (ValueError, TypeError, AttributeError):
        return dict(raw="", error="MISSING_REQUIRED_FIELD")

    body = "%s%s,%s" % (talker, sentence_id, ",".join(fields))
    checksum = pynmea2.NMEASentence.checksum(body)
    return dict(raw="$%s*%02X" % (body, checksum), error="")


# ------------------------------------------------------------- stream decode

def decode_stream(data: str) -> dict:
    data = data or ""
    truncated = False
    if len(data.encode("utf-8", errors="ignore")) > MAX_STREAM_BYTES:
        data = data.encode("utf-8", errors="ignore")[:MAX_STREAM_BYTES].decode("utf-8", errors="ignore")
        truncated = True
    lines = [ln for ln in data.splitlines() if ln.strip()]
    if len(lines) > MAX_STREAM_LINES:
        lines = lines[:MAX_STREAM_LINES]
        truncated = True

    sentences = []
    valid_count = 0
    error_count = 0
    for line in lines:
        kwargs = parse_any(line)
        sentences.append(kwargs)
        if kwargs.get("error"):
            error_count += 1
        elif kwargs.get("checksum_valid"):
            valid_count += 1
    return dict(
        sentences=sentences, valid_count=valid_count,
        error_count=error_count, truncated=truncated,
    )
