# PlaySBC Evolution Plan

PlaySBC is an enterprise-style SIP/RTP and AI voice lab. It is not yet a production-certified SBC. Historical delivery detail belongs in the [release notes](../release/README.md); this page tracks only the current baseline and forward work.

## Current Baseline: v2.5.5

- SIP UDP/TCP/TLS registration and B2BUA calls through local kind and Azure AKS
- RTPengine anchoring, G.711 transcoding, RTP/RTCP, SRTP interworking, NAT learning, and media evidence
- Active-active and failure-injection regression foundations
- OBi1022 and Zoiper registration with verified two-way audio
- One combined PCAP, canonical SIP ladder, `sipmsg.log`, media verdicts, and HTML/archive evidence
- Isolated `kind-playsbc-real-device` lane with guarded LAN advertisement, optional TLS CA verification, and deadlock-free local upgrades
- Rasa, STT, TTS, DTMF, and scripted AI Voice Gateway regression foundations
- RFC 5359 call hold/resume propagation across both B2BUA legs over UDP, TCP, TLS, and RTPengine

### v2.5.5 Regression Closure

- `ha-options-health-recovery` now produces an actual OPTIONS exchange and OPTIONS-only `sipmsg.log` evidence.
- `load-5cps-60s-rtpengine-transcoding` uses a profile-scoped `30000-32999` RTP range, sufficient for the 300-call media load with additional headroom. AKS and real-device media remain fixed at `30000-30049`.
- Mock Rasa profiles run a reachable in-job webhook and fail when fallback is used; fallback is no longer accepted as successful bot evidence.
- Small multi-call and active-active profiles retain readable unified ladders; high-volume load profiles remain intentionally compact.
- Pre-fault PlaySBC logs are retained before pod deletion so media and dialog evidence is not lost with the pod.

The audited v2.5.4 run had 63 passing profiles and two reported failures. All retained PCAPs were readable, SIP evidence was present for every signalling profile, strict SRTP profiles proved negotiated security and both observed RTP directions, and no traceback, invalid CSeq, index error, or SIP parser failure was found. These are regression-evidence results, not blanket protocol certification.

## Primary Track: Production AI Voice Gateway

AI Voice Gateway work is the main product focus from v2.5.5 toward v3.0.0.

### v2.5.5 Foundation

- Return generated TTS as live RTP in the established call, not report-only audio
- Define one streaming adapter contract for Rasa and future bot providers
- Add deterministic STT partial/final results, TTS chunking, timeout, retry, cancellation, and fallback behavior
- Preserve call/media state when a bot or model becomes slow or unavailable
- Add provider health plus STT, bot, TTS, first-audio, and end-to-end latency metrics
- Produce synchronized SIP, RTP/RTCP, transcript, model, action, and audio evidence
- Keep Docker, kind, AKS, real-device, HA, and non-AI regression gates green

### v2.6.x Expansion

- Add multiple bot backends behind the provider interface
- Add multi-turn dialog state, DTMF hybrid IVR, transfer, conference, and human-agent fallback
- Add real Whisper/Vosk and Piper/Coqui images with model warmup and readiness gates
- Add streaming load, interruption, bot-failure, model-failure, and long-call profiles
- Add AI dashboards for provider health, latency percentiles, active sessions, fallback, and errors

### v3.0.0 Acceptance

- Live bidirectional speech loop passes on local kind, AKS, SIPp, and real devices
- Multiple bot integrations run without SIP/media implementation changes
- Call state and fallback behavior are deterministic under provider failures
- Every AI call has complete signalling, media, transcript, model, action, and latency evidence
- Security, privacy, retention, secret rotation, overload, and operational runbooks are validated

## Secondary Track: RFC 5359 Business Calling Services

[RFC 5359](https://www.rfc-editor.org/info/rfc5359/) is a Best Current Practice containing SIP service examples. It does not make a device or SBC compliant by itself. Most examples are user-agent features; some require proxy assistance, and PlaySBC can implement the network side as a B2BUA.

PlaySBC now propagates an in-dialog re-INVITE to the opposite B2BUA leg, preserves dialog routing and CSeq ordering, and updates an existing RTPengine session. Synthetic UDP, TCP, TLS, and RTPengine profiles validate the signalling sequence. Real-device hold/resume remains an acceptance gate before the feature is described as production-ready.

### v2.5.5 Priority: Hold And Resume

- Accept an in-dialog re-INVITE from either call leg and originate the corresponding request on the opposite B2BUA leg
- Validate dialog identifiers, route set, Contact, monotonically increasing CSeq, SDP origin version, retransmissions, and glare handling
- Support `a=sendonly`, `a=recvonly`, and `a=inactive`; tolerate legacy `c=IN IP4 0.0.0.0` while preferring direction attributes
- Update RTPengine offer/answer state without destroying the media session
- Stop and restore the correct RTP direction while keeping RTCP and dialog state coherent
- Complete re-INVITE, `200 OK`, and ACK transactions before changing the service verdict
- Handle BYE, CANCEL-equivalent race conditions, timeout, failed re-INVITE, and repeated hold/resume safely
- Validate both OBi1022-to-Zoiper and Zoiper-to-OBi1022 over UDP first, then TCP/TLS where the device supports it

Synthetic regression profiles:

- `rfc5359-call-hold-resume`
- `rfc5359-call-hold-resume-rtpengine`
- `rfc5359-call-hold-resume-tcp`
- `rfc5359-call-hold-resume-tls`

Planned real-device acceptance profile: `rfc5359-call-hold-resume-real-device`.

Evidence must prove the initial two-way media period, hold SDP and media suppression, resume SDP and restored bidirectional RTP/RTCP, clean teardown, and no leaked RTPengine session.

The v2.5.5 synthetic gate sends bounded PCMU bursts from both call legs before hold and after resume. Its combined PCAP must contain both RTP directions and a measurable media-free hold interval; SIP-only success is rejected.

### Remaining HA Evidence Caveat

The current mid-call PlaySBC pod-delete profiles use Kubernetes' normal termination grace period. They prove call continuity during replacement and now preserve pre-fault logs, but they do not yet prove an abrupt process crash followed by shared-dialog restoration on a surviving node. A future HA gate must force termination, identify the serving node before the fault, prove restoration on a different node, and verify uninterrupted or bounded-loss RTP.

### v2.6.x Service Sequence

| RFC 5359 service | Target | PlaySBC responsibility |
| --- | --- | --- |
| 2.1 Call Hold | v2.5.5 | Re-INVITE/SDP propagation and RTPengine direction update |
| 2.2 Consultation Hold | v2.6.0 | Maintain original dialog while establishing consultation dialog |
| 2.3 Music on Hold | v2.6.0 | Controlled media source, SDP direction, and RTPengine anchoring |
| 2.4 Unattended Transfer | v2.6.1 | REFER, NOTIFY, new dialog, failure recovery, and teardown |
| 2.5 Attended Transfer | v2.6.1 | Consultation dialog plus REFER with Replaces |
| 2.6 Instant Messaging Transfer | Later v2.6.x | Optional MESSAGE-session work; not a real-device voice priority |
| 2.7 Unconditional Forwarding | v2.6.2 | Policy/registrar target selection and loop prevention |
| 2.8 Forwarding on Busy | v2.6.2 | Busy response handling and alternate target routing |
| 2.9 Forwarding on No Answer | v2.6.2 | Ring timeout, cancellation, and alternate target routing |

Every service needs unit tests, local SIPp profiles, kind and AKS regression coverage, combined evidence, and real-device validation when the endpoint exposes the feature.

## Production And Scale Track

Azure remains the first reference cloud; AWS follows.

- Replace lab-only shared state with a replicated registrar/dialog/CDR backend
- Validate production SIP load balancing, affinity, draining, certificate rotation, firewalling, and SRTP policy
- Add malformed SIP, registration storm, OPTIONS storm, INVITE burst, RTP exhaustion, and overload protection
- Add multi-zone failure, backup/restore, rollback, and days-long soak tests
- Progress through 10k, 50k, 100k, then 300k registrations
- Progress through 250, 500, 1000, then 2500 concurrent calls
- Publish measured CPU, memory, CPS, registrations/s, packet rate, media sessions, quality, and recovery time

## Golden Rule

No AI, RFC 5359, HA, cloud, or real-device change may silently regress another lane. Each change needs focused tests, existing-suite compatibility, explicit kube context and image preflight, clean logs, one combined evidence bundle, and an actionable pass/fail verdict.
