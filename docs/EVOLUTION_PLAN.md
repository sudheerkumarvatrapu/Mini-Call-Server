# PlaySBC v2.6.0 Public Baseline

PlaySBC v2.6.0 is the final public MIT feature gate. This page records that baseline only. Historical delivery detail is preserved in the [release notes](../release/README.md); future commercial product planning is outside the public evolution plan.

## Included Baseline

- SIP UDP, TCP, and TLS registration and B2BUA call flows
- Digest REGISTER for synthetic and real-device users
- RTPengine media anchoring, G.711 transcoding, RTP/RTCP, SRTP interworking, and NAT learning
- Local Docker, kind, minikube compatibility, Azure AKS, and isolated local real-device deployment models
- Active-active, node-drain, shared-state, and failure-injection lab foundations
- OBi1022 and Zoiper registration with verified two-way RTPengine-anchored audio
- Rasa, STT, TTS, DTMF, and scripted AI Voice Gateway regression foundations
- RFC 5359 call hold/resume signalling over UDP, TCP, TLS, and RTPengine
- Prometheus metrics and Grafana dashboards
- HTML reports, canonical SIP ladders, `sipmsg.log`, media evidence, and combined packet capture

## v2.6.0 Regression And Evidence Gate

- The full public catalog contains 70 selectable profiles.
- `evidence-b2bua-two-leg-pcap` requires core and peer packet sources plus two distinct B2BUA INVITE Call-IDs.
- Long local macOS runs use a scoped `caffeinate` process to prevent host sleep from creating false SIPp timeouts.
- The Kubernetes launcher reports live `X/70` progress.
- `pcap-legs.json` records expected roles, per-role packet counts, merged packet count, SIP event count, INVITE Call-IDs, and a pass/fail verdict.
- Missing or empty expected capture roles fail evidence collection before split captures are removed.
- High-volume profiles remain intentionally compact and explicitly state when packet capture is omitted.

The three load failures in `k8s-regression-20260827-201206` were traced to host suspension. Caller SIPp completed its workload before delayed peer timeouts. That run does not prove a PlaySBC load defect or a production capacity limit.

## Deployment Baselines

| Lane | Public baseline |
| --- | --- |
| Docker | Fast SIP, media, AI, and negative-profile development checks |
| Local kind | Canonical full 70-profile active-active regression lab |
| Minikube | Compatibility lane; not the canonical full-run topology |
| Local real device | Isolated `kind-playsbc-real-device` cluster using the Mac LAN address |
| Azure AKS | One PlaySBC and one RTPengine readiness topology with Azure LoadBalancers and ACR |
| Real devices on AKS | OBi1022 `1001` and Zoiper `1002` over public SIP and RTP addresses |

## Evidence Contract

Every applicable profile must provide an actionable verdict and the evidence appropriate to its behavior:

- canonical SIP ladder and combined `sipmsg.log`
- `log.sip`, `log.media`, and `log.platform`
- one combined `capture.pcap` for non-load call profiles
- `pcap-legs.json` for merged role and B2BUA-leg certification
- RTP/RTCP, codec, transcoding, SRTP, AI, HA, or failure evidence required by the profile
- HTML and archive output that retains useful logs without unnecessary duplicate PCAPs

## Honest Product Boundary

PlaySBC v2.6.0 is an engineering and interoperability lab, not a production-certified carrier SBC. It does not claim validated support for 300,000 registrations or 2,500 concurrent calls. Production use still requires measured capacity tests, distributed registrar/dialog/CDR state, hardened security and overload controls, multi-zone recovery, operational support, and deployment-specific certification.

The public MIT grant for source and artifacts published through v2.6.0 remains unchanged. Product development after the exact v2.6.0 fork is not part of this public baseline.

## Golden Rule

No public baseline correction may silently weaken Docker, kind, minikube, AKS, HA, AI, observability, or real-device behavior. A correction is acceptable only when affected unit checks, Helm validation, focused protocol checks, and the operator-run deployment regression remain green.
