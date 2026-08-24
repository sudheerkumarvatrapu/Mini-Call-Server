# PlaySBC Evolution Plan

PlaySBC is an enterprise-style SIP/RTP lab and regression platform. It is not yet a production-certified SBC. Production readiness must be earned through measured scale, security, HA, cloud networking, and long-duration validation.

## Current Baseline

### Signalling

- SIP UDP/TCP/TLS with REGISTER, OPTIONS, INVITE, ACK, CANCEL, BYE, and digest authentication
- Registrar-backed B2BUA routing, trunk groups, route policies, normalization, CAC, health probing, and node draining
- Shared registrar/dialog/B2BUA lab state and active-active node identity
- Pre-call, mid-call, post-call, RTPengine failure, drain, restore, and load-distribution regression profiles

### Media

- PCMU/PCMA, transcoding, RFC 4733, RTP/RTCP, and SDES-SRTP/RTP interworking
- RTPengine anchoring, SDP rewrite, public advertised IP, NAT learning, media handover, and packet verdicts
- One combined PCAP, canonical SIP ladder, media classification, and HTML evidence
- Validated two-way OBi1022/Zoiper PCMU calls through AKS

### AI Voice Gateway

- Rasa REST, real Rasa pod, chat/NLU matrices, and guardrail profiles
- Vosk/Whisper STT and Piper/Coqui TTS adapter paths
- Real G.711 speech input, WAV evidence, contact-center sales flow, and long-response chunking

### Platform

- Docker dual-realm regression
- Helm deployment for kind, minikube, and AKS
- Active-active PlaySBC/RTPengine lab topology
- Prometheus/Grafana with node, realm, SIP, media, codec, transcoding, and AI metrics
- AKS public SIP/RTP LoadBalancers and strict cloud readiness profiles

## v2.5.2 Immediate Scope

The next release starts with a local kind real-device lane so registration, calls, media, capture, and HA iteration do not require an expensive AKS session.

### Priority 0: Local Kind Real Devices

- Expose stable SIP UDP/TCP/TLS and RTP/RTCP ports from kind to the home LAN.
- Register the OBi1022 and Zoiper through the local cluster before adding Poly/Yealink devices.
- Prove both call directions with two-way RTP and RTCP, one combined PCAP, one canonical ladder, and a downloadable evidence archive.
- Preserve the existing AKS real-device values and public-IP behavior; local settings must remain a separate profile.
- Add repeatable create, upgrade, monitor, capture, regression, and cleanup commands to the Kubernetes and real-device runbooks.
- Run the existing local Kubernetes, AKS, AI/Rasa, Docker, and real-device gates before release.

### Evidence Caveats To Close

- Remove non-fatal SIPp `SSL_ERROR_WANT_READ` and watchdog notices from final `stderr.log` while retaining raw diagnostics separately.
- Stop requesting previous-container logs when no previous container exists, eliminating Kubernetes `BadRequest` text from pod evidence.
- Collect and validate AKS advertised-IP evidence after each profile Helm rollout, not only before the profile transition.
- Scope PlaySBC logs to the regression window and regression call IDs so unrelated public real-device REGISTER attempts do not enter profile evidence.
- Make `archive-manifest.txt` either a complete checksum inventory or explicitly label its current 200-path preview, and reconcile pre-manifest versus archived file counts.
- Keep the current strict requirement for one merged `capture.pcap`, one `sipmsg.log`, complete ladders, bidirectional media verdicts, and zero packet drops.

The v2.5.1 AKS run `aks-regression-20260824-172526` passed all 12 profiles and every strict evidence validator. These items improve evidence clarity and timing; they are not signalling or media failures in that run.

## Next Architecture: Local Multi-Node HA Lab

This follows the local real-device baseline and moves expensive HA/failover iteration from AKS to a repeatable local environment.

```text
kind control-plane
├── worker-1: PlaySBC-0 + RTPengine-0
└── worker-2: PlaySBC-1 + RTPengine-1
```

### Priority 0

- Create a reproducible kind configuration with one control-plane and two workers.
- Pin each PlaySBC/RTPengine pair to separate workers with pod anti-affinity.
- Add PodDisruptionBudgets and controlled node drain behavior.
- Provide shared registrar/dialog state that works across workers; SQLite/RWO remains lab-only, so RWX or Redis/PostgreSQL must be evaluated.
- Run all existing HA profiles through the multi-node topology.
- Kill PlaySBC-0, RTPengine-0, and worker-1 during active calls and record recovery behavior.
- Prove active-active load distribution and restored registrar/dialog ownership.
- Add Grafana panels for worker, PlaySBC node, RTPengine pair, drain state, failover count, and recovery time.
- Keep one canonical SIP/RTP/RTCP PCAP and a clear four-node ladder.

### Acceptance Gates

- Existing Docker, single-node kind/minikube, AKS, Rasa, and real-device regressions remain green.
- A failed image or missing variable cannot mutate a healthy deployment.
- Pod failure and node drain have deterministic report verdicts.
- Mid-call tests distinguish signalling recovery from true media continuity.
- The runbook can create, test, inspect, and delete the lab without manual repair.

### Scope Boundary

Multi-node kind validates Kubernetes scheduling, pod/node disruption, shared state, and application recovery on one Mac. It does not prove Azure zone failure, physical host failure, or production load-balancer behavior. AKS remains the release-milestone lane for those cloud-specific checks.

## Near-Term Work

### HA And Networking

- Extend restored mid-call handling to CANCEL, re-INVITE, REFER, and transfer flows.
- Promote RTPengine mid-call recovery toward lossless continuity where Sipwise session ownership permits it.
- Add real core/peer interfaces with Multus or another multi-network CNI.
- Define external SIP affinity, health steering, and graceful drain behavior.
- Replace SQLite lab HA state with Redis/PostgreSQL or another replicated backend.

### Real Devices

- Validate OBi1022 and future Poly/Yealink devices over TCP and TLS.
- Add longer calls, re-registration during calls, SIP ALG detection, and multi-device scenarios.
- Run local-LAN real-device tests through a dedicated kind cluster with one-to-one SIP and RTP port mappings.
- Add richer RTCP loss/jitter and MOS-style evidence.

### AI Voice Gateway

- Return generated TTS RTP into the live call, not only report evidence.
- Add real model images for Whisper and Coqui.
- Add action-server workflows, multi-turn state, DTMF hybrid IVR, transfer, and barge-in.
- Add STT, Rasa, TTS, streaming, fallback, and action latency metrics.

## Production Cloud Track

Azure remains the first production reference cloud; AWS follows.

- External shared state for registrar, dialog, transaction, CDR, audit, and billing events
- Production SIP load balancing and affinity for UDP/TCP/TLS
- Certificate lifecycle, secret rotation, SRTP/DTLS-SRTP policy, and firewall controls
- SIP flood, malformed-message, registration storm, OPTIONS storm, INVITE burst, and overload protection
- Multi-AZ deployment, failure injection, backup/restore, upgrade/rollback, and days-long soak runs
- Capacity progression: 10k, 50k, 100k, then 300k registrations; 250, 500, 1000, then 2500 concurrent calls
- Measured CPU, memory, packets per second, RTP sessions, registrations, dialogs, and calls per second

## Production Readiness Gates

- No critical signalling, media, HA, security, or evidence caveats
- Full regression passes on local multi-node and cloud reference topologies
- Load and soak tests pass with packet, media, CDR, and observability proof
- Security scans, fuzzing, malformed SIP, dependency, image, and configuration scans pass
- Operators have tested deploy, scale, drain, failover, backup, restore, upgrade, rollback, and incident procedures

## Delivery Rule

Every change must preserve the golden rule: Docker regression, local Kubernetes, AKS regression, AI/Rasa, real-device behavior, and other deployment models must not regress. New behavior needs focused tests, clear logs, combined evidence, and an actionable report verdict.

Historical version-by-version milestones remain in [release notes](../release/README.md).
