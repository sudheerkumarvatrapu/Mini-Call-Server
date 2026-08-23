# PlaySBC v2.5.0

PlaySBC v2.5.0 makes real-device evidence easier to trust and begins the hardphone TCP/TLS registration track without changing the proven UDP/RTP call path.

## Clean Real-Device Evidence

- Keep one untouched combined `capture.pcap` as the wire-level source of truth.
- Render `sipmsg.log` as a canonical call flow and move duplicate UDP transactions into a retransmission annotations section.
- Collapse near-simultaneous public-LB/pod-interface mirror copies without counting them as SIP retransmissions.
- Classify repeated INVITE `200 OK` after ACK as expected SIP-over-UDP retransmission behavior.
- Separate PCMU/PCMA speech RTP from tiny NAT probes, telephone events, RTCP, and unknown media packets.
- Record pre-answer voice/probe counts, media flows, RTPengine two-direction verdicts, and truthful `bidirectional`, `endpoint-limited`, or `not-observed` RTCP status.
- Add `canonical-sip.json`, `media-evidence.log`, `media-evidence.json`, and a compact `latest.html` to each manual real-device bundle.
- Collect PlaySBC and RTPengine logs from the exact packet-capture start timestamp so earlier calls do not leak into the bundle.

## TCP/TLS Registration Foundation

- Add `register-auth-tcp`, a digest REGISTER-only profile over SIP/TCP.
- Add `register-auth-tls`, a digest REGISTER-only profile over TLS 1.2+ with generated certificate evidence.
- Include both profiles in the common full regression catalog and the AKS profile set.
- Leave OBi1022/Zoiper UDP signalling and RTPengine-anchored G.711 media behavior unchanged.

## Compatibility Contract

- The profile definitions are shared by Docker dual-realm, local regression, kind/minikube, and AKS runners.
- Existing Kubernetes active-active defaults and AKS single-workload readiness defaults remain unchanged.
- Existing Rasa/AI voice, RTPengine, SRTP, HA, load, and observability profile behavior is unchanged.
- The local Kubernetes playbook now carries the complete v2.5.0 active-active upgrade, observability rollout, and published-image full-regression command. Future releases must update it with the AKS and real-device playbooks.

## Validation

- Python compile checks pass for all changed tools.
- The complete `tests.test_sipp_harness` suite passes: 161 tests.
- The combined SIP server, RTPengine, and SIPp harness gate passes: 266 tests with one expected platform skip.
- TCP and TLS registration profile dry-runs render registration-only commands successfully.
- Live Docker dual-realm execution still requires Docker Desktop to be running; the release branch records no protocol failure from that unavailable local daemon.
