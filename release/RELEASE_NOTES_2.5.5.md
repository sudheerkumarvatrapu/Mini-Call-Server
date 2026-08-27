# PlaySBC v2.5.5

PlaySBC v2.5.5 closes the two failures from the 65-profile local Kubernetes run and introduces the first RFC 5359 business-calling profiles without changing the proven AKS or real-device public media contract.

## Regression Closure

- Make `ha-options-health-recovery` execute and retain a real OPTIONS/200 exchange.
- Give `load-5cps-60s-rtpengine-transcoding` a profile-scoped `30000-32999` RTPengine range for 300 concurrent media sessions plus growth headroom.
- Keep AKS and real-device RTP exposure unchanged at `30000-30049`.
- Preserve pre-fault logs before HA pod deletion.
- Restore unified ladders for small multi-call profiles while keeping load evidence compact.

## RFC 5359 Hold And Resume

- Propagate in-dialog re-INVITEs across both B2BUA legs.
- Enforce increasing CSeq and reject overlapping dialog refreshes.
- Preserve `sendonly`, `recvonly`, `inactive`, and `sendrecv` SDP direction state.
- Update existing RTPengine sessions during hold and resume.
- Add UDP, RTPengine, TCP, and TLS hold/resume SIPp profiles with canonical ladder and SIP evidence validation.
- Send short PCMU bursts from both SIPp legs before hold and after resume; require the combined PCAP to prove bidirectional RTP and a held-media gap.

## AI Evidence

- Run mock Rasa inside the Kubernetes regression runner with a reachable pod address.
- Fail mock Rasa profiles when REST fallback or missing transfer evidence is observed.

## Evidence Hardening

- Preserve one combined PCAP and canonical `sipmsg.log` per signalling profile.
- Run OPTIONS-only tcpdump sessions in immediate mode and bound them to the request/response pair so short exchanges close and flush before capture collection.
- Validate RFC 5359 CSeq, ACK, and SDP direction transitions explicitly.
- Keep the runtime `Server` banner synchronized with release metadata.
- Keep readable ladders for low-volume multi-call profiles and compact evidence for high-volume load.

## Compatibility

- AKS LoadBalancer, static SIP/RTP IP, and `30000-30049` real-device values are unchanged.
- Local `kind-playsbc`, minikube, active-active, observability, non-AI SIPp, and real-device paths retain their existing topology contracts.

## Local Real-Device Lab

- Retain the dedicated `kind-playsbc-real-device` context, host-port safeguards, Recreate rollout strategy, TLS behavior, and proven two-way RTP/RTCP path from v2.5.4.

## Validation

- 325 unit and harness tests pass.
- All modified Python modules compile and the Git diff passes whitespace validation.
- The prior 65-profile evidence set was audited for SIP logs, readable combined PCAPs, RTP/RTCP evidence, SRTP verdicts, and severe runtime signatures.

## Known Evidence Limit

Normal Kubernetes pod termination proves replacement continuity but is not yet proof of abrupt crash recovery on a different PlaySBC node. That stricter HA acceptance gate remains tracked.
