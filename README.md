# nmea-tools

Parse, validate, and encode **NMEA 0183** marine/GPS sentences — built for the
[Axiom](https://axiomide.com) marketplace under the `christiangeorgelucas` handle.

Wraps [pynmea2](https://github.com/Knio/pynmea2) (MIT, zero runtime
dependencies) for the sentence protocol; this package adds a canonical
`NmeaSentence` envelope, structured error handling, checksum-independent
validation, sentence encoding, and multi-sentence stream normalization on top.

## Use it from your agent or app

Every node in this package is a **live, auto-scaling API endpoint** on the
[Axiom](https://axiomide.com) marketplace — call it from an AI agent or your own
code, with nothing to self-host.

**📦 See it on the marketplace:**
https://dev.axiomide.com/marketplace/christiangeorgelucas/nmea-tools@0.1.0

**Hook it up to an AI agent (MCP).** Add Axiom's hosted MCP server to any MCP
client and every node becomes a typed tool your agent can call — search the
catalog, inspect a schema, and invoke it directly.

```bash
# Claude Code
claude mcp add --transport http axiom https://api.axiomide.com/mcp \
  --header "Authorization: Bearer $AXIOM_API_KEY"
```

Claude Desktop, Cursor, or any config-based client:

```json
{
  "mcpServers": {
    "axiom": {
      "type": "http",
      "url": "https://api.axiomide.com/mcp",
      "headers": { "Authorization": "Bearer YOUR_AXIOM_API_KEY" }
    }
  }
}
```

**Call it from the CLI.**

```bash
axiom invoke christiangeorgelucas/nmea-tools/ParseSentence --input '{ ... }'
```

**Call it over HTTP.**

```bash
curl -X POST https://api.axiomide.com/invocations/v1/nodes/christiangeorgelucas/nmea-tools/0.1.0/ParseSentence \
  -H "Authorization: Bearer $AXIOM_API_KEY" \
  -H 'Content-Type: application/json' \
  -d '{ ... }'
```

> Input/output schema for each node is on the marketplace page above, or via
> `axiom inspect node christiangeorgelucas/nmea-tools/ParseSentence`.

### Get started free

Install the CLI:

```bash
# macOS / Linux — Homebrew
brew install axiomide/tap/axiom

# macOS / Linux — install script
curl -fsSL https://raw.githubusercontent.com/AxiomIDE/axiom-releases/main/install.sh | sh
```

**Windows:** download the `windows/amd64` `.zip` from the
[releases page](https://github.com/AxiomIDE/axiom-releases/releases), unzip it,
and put `axiom.exe` on your `PATH`.

Then `axiom version` to verify, `axiom login` (GitHub or Google) to authenticate,
and create an API key under **Console → API Keys**. Docs and sign-up at
**[axiomide.com](https://axiomide.com)**.

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
