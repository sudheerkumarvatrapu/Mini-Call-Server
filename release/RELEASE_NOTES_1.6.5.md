# PlaySBC v1.6.5

Real-device AKS diagnostics and media exposure hotfix for OBi1022 and Zoiper validation.

## Fixed

- Emits route candidate, route selected, SIP TX response, ACK forwarding, BYE forwarding, and RTPengine evidence to `kubectl logs` when AKS persistent call logs are disabled.
- Accepts common hardphone target formats such as uppercase `SIP:`, `tel:` URIs, and display-name extension fallback when the Request-URI points at the SBC public IP.
- Keeps B2BUA ACK forwarding tolerant for active calls when real endpoint dialog headers are less strict than the lab SIPp flows.
- Keeps B2BUA BYE clearing tolerant so either leg can clear the other leg and receive `200 OK`.
- Returns `484 Address Incomplete` for truly incomplete proxy-style INVITEs, and `404 Not Found` for complete but unroutable extensions.

## Azure RTP

- Adds `cloud.azure.media.public.portRange` to expose a compact UDP RTP range through Azure LoadBalancer without listing every port manually.
- Documents using plain RTP/UDP for the first OBi/Zoiper real-device lab; SRTP/DTLS remains a separate TLS/SRTP profile.

## Validation

- `python3 -m unittest tests.test_mini_call_server`
- `python3 -m py_compile mini_call_server.py`
- `helm lint charts/playsbc`
- `git diff --check`
