# PlaySBC v2.2.2

Real-device AKS media hardening for OBi1022 and Zoiper labs.

## What Changed

- Locked Azure AKS RTP media to UDP `30000-30049` across RTPengine and the Azure RTP public LoadBalancer.
- Added Helm validation so Azure public RTP deployments fail if the RTPengine range, LoadBalancer range, or RTPengine advertised IP is missing or mismatched.
- Added RTPengine media-handover NAT learning for real-device AKS calls.
- Added explicit SDP/RTP evidence:
  - inbound offer SDP summary
  - outbound offer SDP summary
  - callee answer SDP summary
  - caller answer SDP summary
  - RTPengine allocated RTP/RTCP ports
  - RTPengine learned endpoint and packet verdict summary
- Extended AKS regression preflight evidence with RTPengine pod advertised-IP validation.
- Updated Azure AKS and real-device lab runbooks for the stricter media topology.

## Deployment Notes

For real OBi1022/Zoiper testing, keep:

```text
rtpengine.rtpMin=30000
rtpengine.rtpMax=30049
cloud.azure.media.public.portRange=30000-30049
rtpengine.advertisedIP=<RTP public LoadBalancer IP>
playsbc.config.rtpengine_g711_only=true
playsbc.config.rtpengine_plain_rtp_sdp=true
playsbc.config.rtpengine_sip_source_address=true
playsbc.config.rtpengine_media_handover=true
```

The chart intentionally fails fast if Azure public RTP media is enabled but the range or advertised IP is not aligned.
