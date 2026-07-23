# nmea-tools

Parse, validate, and encode **NMEA 0183** marine/GPS sentences — built for the
[Axiom](https://axiomide.com) marketplace under the `christiangeorgelucas` handle.

Wraps [pynmea2](https://github.com/Knio/pynmea2) (MIT, zero runtime
dependencies) for the sentence protocol; this package adds a canonical
`NmeaSentence` envelope, structured error handling, checksum-independent
validation, sentence encoding, and multi-sentence stream normalization on top.

## Nodes

- **ParseSentence** — parse any of pynmea2's ~70 recognized talker sentence
  types; full structured fields for the seven core types below, identity +
  checksum for the rest.
- **ValidateChecksum** — validate a sentence's `*HH` checksum independent of
  whether its type is modeled in structured detail.
- **ParseGGA** — GPS fix data: position, fix quality, satellites, HDOP,
  altitude, geoid separation.
- **ParseRMC** — recommended minimum: position, UTC date+time, status, speed,
  course, magnetic variation.
- **ParseGLL** — geographic position: lat/lon, UTC time, status.
- **ParseVTG** — track made good and ground speed (true + magnetic).
- **ParseGSA** — DOP and active satellites (fix dimension, PRNs, PDOP/HDOP/VDOP).
- **ParseGSV** — satellites in view (PRN, elevation, azimuth, SNR), paged.
- **ParseZDA** — UTC date/time and local time zone offset.
- **EncodeSentence** — build a well-formed, checksummed sentence from
  structured fields (GGA/RMC/GLL/VTG/GSA/ZDA).
- **DecodeStream** — normalize a multi-line NMEA session log into an ordered
  list of decoded sentences, one bad line never failing the whole batch.

Coordinates are decimal degrees on the WGS-84 datum (field names `lat`/`lon`),
matching `christiangeorgelucas/geo-tools` and `christiangeorgelucas/gpx-tools`
so a decoded fix composes directly into either package.

## License

MIT — see [LICENSE](./LICENSE).
