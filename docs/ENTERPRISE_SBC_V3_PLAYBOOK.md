# PlaySBC v2.6+ Commercial And v3 Enterprise SBC Playbook

This playbook defines the commercial product track that begins with PlaySBC v2.6.0 and grows into the v3 Enterprise SBC. Version 2.6.x delivers private production Voice AI capabilities; v3 combines the fully functional AI Voice Gateway with the SIP, security, HA, scale, and operational controls required for an enterprise SBC.

PlaySBC v2.5.5 is the final public MIT feature release and remains an engineering and regression lab. Nothing in this plan describes the current v2.5.5 code as production-certified.

## Distribution And License Boundary

- Existing releases and source published through v2.5.5 under the MIT License remain available under those granted MIT terms.
- PlaySBC v2.5.5 is the final public MIT feature gate. New Voice AI, enterprise SBC, and related product capabilities developed for v2.6.0 and later are planned for private distribution under a separate paid commercial license, not the MIT license.
- Commercial modules, images, charts, model adapters, documentation, and release artifacts must use private repositories and registries with authenticated customer access.
- Proprietary v2.6+ implementation must not be committed to the public MIT repository or included in a public MIT image by accident.
- The final commercial EULA, third-party model terms, support policy, and dependency notices require legal review before the first v2.6.0 commercial release.

This boundary does not revoke or restrict rights already granted for published MIT code through v2.5.5.

## v2.6.0 Commercial Development Gate

Before implementing v2.6.0 product code:

1. Create a private source repository or other access-controlled commercial development location from the v2.5.5 baseline.
2. Add the commercial license and third-party notices before the first private release.
3. Use private container, Helm, model, evidence, and documentation registries.
4. Restrict CI/CD credentials and artifacts to authorized developers and customers.
5. Keep the public MIT repository on the v2.5.5 feature line; do not run public image-release workflows for v2.6+ commercial tags.
6. Maintain an explicit provenance record identifying reusable MIT baseline code and newly developed commercial code.

Gate status as of 2026-08-28: the access-controlled commercial repository was
created from the exact public `v2.5.5` commit and tree; commercial and retained
MIT license notices, third-party inventory, provenance ledger, private artifact
namespaces, least-privilege CI policy, and manual commercial release controls
are in place. The public image workflow is manual and rejects every version
other than `2.5.5`. Branch and environment approval rules for private
repositories require a GitHub plan that supports those controls; until that is
enabled, repository membership remains owner-only and commercial releases are
owner-operated through the dedicated environment.

Public v2.5.x maintenance may receive documentation, security, or compatibility corrections, but new Voice AI and Enterprise SBC product features belong only in the private commercial track.

## v3.0.0 Enterprise Entry Gate

Work enters the enterprise v3 phase only after the private commercial v2.6.x foundation proves:

- generated TTS returned as live RTP in an established call
- deterministic streaming STT, bot, and TTS provider contracts
- timeout, retry, cancellation, fallback, and slow-provider behavior
- synchronized SIP, RTP/RTCP, transcript, model, action, latency, and audio evidence
- green Docker, kind, AKS, real-device, HA, AI, and non-AI regression lanes
- no unresolved regression or real-device caveat carried silently into v3

## v3.0.0 Product Foundation

### Production AI Voice Gateway

- Bidirectional streaming audio between SIP callers and the selected AI provider
- Provider-neutral adapters for Rasa and future bot, STT, TTS, and model platforms
- Multi-turn state, barge-in, interruption, RFC 4733 DTMF, transfer, conference, human handoff, and controlled release
- Provider health, warmup, readiness, circuit breaking, backpressure, and capacity controls
- Per-stage STT, bot, TTS, first-audio, interruption, fallback, and end-to-end latency metrics
- Privacy, retention, transcript redaction, secret rotation, tenant isolation, and audit controls

### SIP Transaction And Dialog Core

- Complete RFC 3261 transaction timers, retransmissions, duplicate suppression, and branch matching
- Forked INVITEs, multiple early dialogs, multiple final responses, and redirect handling
- Correct CANCEL/487/ACK, BYE, re-INVITE, target-refresh, and overlapping-request races
- Record-Route/Route processing, loose routing, remote-target changes, and dialog restoration
- Reliable provisional responses, `100rel`, PRACK, and early-media interworking
- Session timers, `Session-Expires`, `Min-SE`, refresh ownership, `422`, and SIP UPDATE
- Fuzz, malformed-message, oversized-message, and parser resource-limit gates

### Enterprise Registrar And NAT

- Multiple contacts per AOR, per-contact expiry, wildcard deregistration, and REGISTER Call-ID/CSeq ordering
- Replicated registration storage with conflict handling, backup, restore, and multi-zone recovery
- SIP Outbound, Path, connection reuse, flow tokens, keepalive, failover, and GRUU
- UDP, TCP, and TLS NAT behavior proven across hardphones, softclients, PBXs, and cloud trunks
- Registration storm protection and measured registration refresh capacity

### Routing And Interworking

- DNS NAPTR/SRV/A resolution, weighted targets, health probing, and deterministic failover
- Route groups, tenant dial plans, number normalization, policy routing, and loop prevention
- Per-trunk authentication, TLS, identity, codec, SDP, privacy, and admission policies
- SIP response and telephony cause mapping with retry and alternate-route policy
- Consultation hold, music on hold, unattended and attended transfer, and call forwarding

### Security And Trust Boundary

- Mutual TLS, trust stores, hostname verification, certificate rotation, and revocation policy
- SHA-256-class digest authentication, nonce lifetime, replay prevention, lockout, and credential rotation
- ACLs, topology hiding, trusted identity domains, privacy headers, and tenant isolation
- Registration, OPTIONS, INVITE, malformed SIP, and media-exhaustion rate controls
- STIR/SHAKEN signing and verification where the deployment and jurisdiction require it
- Software bill of materials, signed images, provenance, vulnerability gates, and release attestation

### HA, Scale, And Operations

- Replicated registrar, transaction, dialog, media, and CDR state without SQLite or single-worker ownership
- Abrupt process, pod, node, zone, provider, database, and RTPengine failure tests
- Active-call draining, ownership transfer, bounded-loss recovery, rollback, and disaster recovery
- Progressive gates for 10k, 50k, 100k, and 300k registrations
- Progressive gates for 250, 500, 1000, and 2500 concurrent calls
- Measured CPS, registrations per second, packet rate, latency, quality, resource use, and recovery time
- Multi-day soak, overload, chaos, upgrade, downgrade, backup, and restore evidence

## Delivery Sequence

| Milestone | Required outcome |
| --- | --- |
| v2.6.0 | Private commercial development boundary plus live TTS RTP, streaming provider contract, deterministic failure handling, synchronized evidence, and green compatibility gates |
| v2.6.x | Multiple private AI providers, multi-turn workflows, interruption, DTMF, transfer, human handoff, production model images, and AI observability |
| v3.0.0 | Commercial packaging, fully functional AI Voice Gateway, hardened SIP transaction/session core, security baseline, and green compatibility gates |
| v3.1.x | Enterprise registrar, SIP Outbound/NAT, trunk routing, business calling, and expanded device/PBX interoperability |
| v3.2.x | Distributed HA state, multi-zone recovery, scale milestones, overload control, and operational automation |
| Later v3.x | Carrier identity, regulatory integrations, external certification, broader cloud support, and measured production references |

## Mandatory Regression Matrix

Every commercial change must pass the applicable lanes before release:

| Lane | Required proof |
| --- | --- |
| Unit and protocol | Transaction, dialog, parser, policy, provider, and failure-state behavior |
| Docker | Fast SIP, media, AI, negative, and compatibility profiles |
| Local kind | Full catalog, active-active, abrupt HA, observability, and upgrades |
| AKS | Azure networking, public/private SIP and RTP, identity, load balancers, and rollback |
| Real devices | Registration, calls, hold, transfer, DTMF, two-way RTP/RTCP, TLS, and NAT |
| Scale and soak | Published topology, workload, duration, capacity, quality, and failure evidence |

Evidence must include one synchronized bundle containing the verdict, canonical SIP ladder, `sipmsg.log`, combined PCAP where practical, media verdicts, provider events, transcript/action timeline, metrics snapshot, configuration fingerprint, and image digests.

## Release Acceptance

A commercial v2.6+ or enterprise v3 release is not ready until:

1. Every advertised feature has an automated positive, negative, timeout, recovery, and interoperability test.
2. No release depends on fallback behavior to report a false pass.
3. Active calls and registrations have documented behavior for every supported failure class.
4. Security, privacy, retention, upgrade, rollback, backup, and recovery procedures are exercised.
5. Capacity statements are based on repeatable measurements rather than extrapolation.
6. Commercial licensing, third-party terms, support boundaries, and customer artifacts are complete.

## Golden Rule

No AI, SIP, media, HA, cloud, security, scale, or real-device implementation may weaken another regression lane. A feature is delivered only when its behavior and synchronized evidence are both green.
