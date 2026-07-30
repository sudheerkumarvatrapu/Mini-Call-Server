# PlaySBC v2.0.0

Real-device AKS lab baseline for OBi1022 and Zoiper.

## Major Milestone

- Validates real-device SIP registration and B2BUA calls through Azure AKS.
- Anchors media with RTPengine for internet-facing OBi1022 and Zoiper calls.
- Keeps public SIP advertised addresses dynamic through the current Azure LoadBalancer IP.
- Keeps missing registered routes strict so PlaySBC does not fall back to echo SDP for real devices.

## Fixed

- Adds `b2bua_invite_timeout` so a real hardphone can ring long enough before PlaySBC returns `480 Temporarily Unavailable`.
- Adds `rtpengine_g711_only` for the first OBi/Zoiper media baseline, clamping broad endpoint SDP to G.711 plus telephone-event before RTPengine offer/answer.
- Logs RTPengine codec clamp, route selection, SIP responses, ACK/BYE forwarding, timeout seconds, and media query evidence to pod stdout.

## Real Device Lab Settings

Recommended AKS real-device values:

```bash
--set playsbc.config.reject_unknown_routes=true
--set playsbc.config.b2bua_invite_timeout=60.0
--set playsbc.config.rtpengine_g711_only=true
--set-string playsbc.config.sip_advertised_ip="$SIP_PUBLIC_IP"
--set-string playsbc.config.b2bua_advertised_ip="$SIP_PUBLIC_IP"
--set-string rtpengine.advertisedIP="$RTP_PUBLIC_IP"
```

## Validation

- `python3 -m unittest tests.test_mini_call_server`
- `python3 -m py_compile mini_call_server.py`
- `helm lint charts/playsbc`
- `helm template charts/playsbc`
- `git diff --check`
