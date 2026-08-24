# PlaySBC v2.5.1

PlaySBC v2.5.1 fixes the two mixed SRTP AKS regression profiles by making the synthetic secure endpoint a supervised runner process instead of an embedded SIPp shell action.

## Root Cause

- `tls-srtp-to-udp-rtp` and `udp-rtp-to-tls-srtp` completed SIP signalling and RTPengine delivered encrypted media to the secure endpoint pod.
- The secure endpoint returned zero packets because SIPp passed its embedded helper command to `sh`, which rejected the background operator with `Syntax error: "&" unexpected`.
- SIPp still exited `0`, so the helper failure was visible only in stderr while strict media evidence correctly failed the profile.

## Fix

- Remove executable commands from rendered SIPp XML; secure scenarios now contain SDP only.
- Start `send_srtp_audio.py` explicitly in the secure core or peer endpoint before the call.
- Track the helper command, stdout, stderr, timeout, and exit status as profile evidence.
- Fail the profile when the helper cannot bind, times out waiting for RTPengine, or exits nonzero.
- Apply the same lifecycle to AKS/kind Kubernetes, Docker dual-realm, and direct local smoke runners.
- Keep deterministic secure RTP/RTCP ports `6000-6001`, authenticated AES-CM/HMAC-SHA1-80 traffic, and plain-leg dynamic RTP behavior.

## Compatibility

- Real-device OBi1022/Zoiper signalling and RTPengine media configuration are unchanged.
- Plain RTP, RTP/RTCP, transcoding, AI/Rasa, HA, load, Grafana, and Prometheus paths are unchanged.
- Helm values retain the existing AKS SIP/RTP LoadBalancer and `30000-30049/UDP` RTPengine range.

## Validation

- Latest failed AKS bundle was traced across generated XML, SIPp stderr, RTPengine query results, and both packet directions.
- Focused secure-rendering and Kubernetes process-placement tests pass.
- Complete repository test gate passes: 315 tests with one expected platform skip.
- The next AKS run must prove both secure profiles return encrypted packets and pass strict RTPengine bidirectional evidence.
