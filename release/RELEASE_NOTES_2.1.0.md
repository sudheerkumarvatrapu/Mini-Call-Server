# PlaySBC v2.1.0

Real-device media hardening for the AKS OBi1022 and Zoiper lab.

## What changed

- Adds `rtpengine_sip_source_address` so PlaySBC can ask RTPengine to use the observed SIP source address for NAT endpoint learning.
- Forces `RTP/AVP` toward RTPengine when `rtpengine_plain_rtp_sdp=true`.
- Sends `ICE=remove` to RTPengine for plain-RTP real-device calls, instead of only cleaning ICE/RTCP-mux from the returned SDP text.
- Keeps the existing G.711-only and plain-RTP SDP cleanup for OBi1022/Zoiper baseline testing.
- Updates AKS and real-device runbooks for the v2.1.0 upgrade path.

## Why

Zoiper -> OBi1022 had two-way RTP, but OBi1022 -> Zoiper could complete SIP signalling with `0` RTP packets in RTPengine. The weak point was real-device NAT media learning and RTPengine's internal ICE/plain-RTP state. v2.1.0 makes that path explicit for internet phones behind home NAT.

## AKS real-device settings

Use these together for the OBi1022/Zoiper baseline:

```bash
--set playsbc.config.rtpengine_g711_only=true
--set playsbc.config.rtpengine_plain_rtp_sdp=true
--set playsbc.config.rtpengine_sip_source_address=true
```

## Validation

- Unit tests cover RTPengine `SIP source address`, `received from`, `ICE=remove`, and config parsing.
- Helm chart version and app version are `2.1.0`.
