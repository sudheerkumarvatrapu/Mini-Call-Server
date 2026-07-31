# PlaySBC v2.1.1

Real-device media hotfix for OBi1022 and Zoiper calls through AKS + RTPengine.

## Why This Release Exists

The v2.1.0 real-device path improved RTPengine NAT learning and plain RTP SDP handling, but the OBi1022 still sent in-dialog re-INVITEs during answered calls. PlaySBC treated those refresh INVITEs as new dialogs and returned `491 Request Pending`, which could stop OBi-originated RTP from starting.

## What Changed

- Accept caller-leg in-dialog re-INVITEs for active B2BUA calls.
- Reuse the cached caller-side SDP answer so real devices receive a valid `200 OK` SDP answer for media refreshes.
- Consume ACKs for locally answered re-INVITEs instead of forwarding them to the peer leg.
- Preserve normal initial ACK, BYE, registrar routing, and RTPengine NAT learning behavior.
- Add focused unit coverage for the OBi-style `8002 INVITE` / `8002 ACK` refresh path.

## Validation

- `python3 -m py_compile mini_call_server.py rtp/rtpengine.py`
- Focused B2BUA real-device signalling tests pass.
- `helm lint charts/playsbc`

## AKS Upgrade Notes

Use the v2.1.1 Helm chart and images for OBi1022 <-> Zoiper validation. Keep RTPengine plain RTP/NAT learning enabled:

- `rtpengine_g711_only=true`
- `rtpengine_plain_rtp_sdp=true`
- `rtpengine_sip_source_address=true`

