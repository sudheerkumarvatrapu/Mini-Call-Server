# PlaySBC v1.6.1

PlaySBC `v1.6.1` is a real-device AKS lab release for OBi1022 and Zoiper testing.

## What Changed

- Registrar-backed routes now detect private, loopback, link-local, or unspecified Contact hosts and send outbound packets to the observed REGISTER source address.
- SIP responses now add `received=` and fill bare `rport` in the top Via header for NAT-facing UDP clients.
- B2BUA outbound INVITE logs now include the actual packet destination chosen for the outbound leg.
- Added the Real Device Lab runbook for OBi1022 `1001` and Zoiper `1002` registration/call testing through AKS.
- Azure AKS docs now capture the practical hurdles found during the hardphone lab.
- Chart and reference image tags move to `1.6.1`.

## Why

The first OBi1022 registration succeeded through Azure AKS, but the phone correctly advertised a private LAN Contact:

```text
Registered 1001 -> sip:1001@192.168.1.9:5060
```

For inbound calls to that device, PlaySBC must not send packets only to `192.168.1.9`. The v1.6.1 routing path keeps the SIP Contact as the Request-URI but sends the packet to the observed public REGISTER source. That makes the AKS home-hardphone lab usable without manual router port forwarding for the first SIP signalling tests.

## Real Device Notes

- OBi1022 Profile A should use the AKS public SIP IP, UDP `5062`, `X_DnsSrv=false`, and `X_UseTokenAuth=false`.
- OBi1022 SP1 should use `AuthUserName=1001`, `AuthPassword=secret-password`, `URI=1001`, and Profile `A`.
- Zoiper can register as `1002` against the same AKS public SIP IP and port.
- SIPp `OPTIONS` and digest `REGISTER` remain useful preflight checks before troubleshooting a physical phone.

## Artifacts

- Helm chart: `playsbc-1.6.1.tgz`
- PlaySBC image: `ghcr.io/sudheerkumarvatrapu/playsbc:1.6.1`
- RTPengine image: `ghcr.io/sudheerkumarvatrapu/playsbc-rtpengine:1.6.1`
- Regression runner image: `ghcr.io/sudheerkumarvatrapu/playsbc-k8s-regression:1.6.1`
- SIPp image: `ghcr.io/sudheerkumarvatrapu/playsbc-sipp:1.6.1`

## Validation

- `python3 -m unittest tests.test_mini_call_server`
- `python3 -m py_compile mini_call_server.py`
- `git diff --check`
- Helm chart package generated under `release/helm/`
