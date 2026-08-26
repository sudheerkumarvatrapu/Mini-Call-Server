# PlaySBC v2.5.2

PlaySBC v2.5.2 adds a dedicated local kind real-device connectivity lane and closes evidence-noise caveats without changing the validated AKS, active-active kind, Docker, or AI/Rasa profile contracts.

## Local Real-Device Lab

- Add a separate `playsbc-real-device` kind cluster with one-to-one host mappings for SIP `5062/UDP`, `5062/TCP`, TLS `5061/TCP`, and RTP/RTCP `30000-30049/UDP`.
- Add a guarded single PlaySBC plus single RTPengine values profile that advertises the Mac LAN IPv4 address.
- Add a preflight checker for cluster identity, all 53 Docker port/protocol bindings, replica readiness, host networking, DNS policy, images, SIP configuration, RTP range, and RTPengine advertised IP.
- Pin manual capture commands to an explicit kube context so local and AKS evidence cannot be mixed accidentally.
- Preserve the existing combined PCAP, canonical SIP ladder, RTP/RTCP verdict, HTML, and `.tgz` evidence workflow.

## Evidence Hardening

- Remove non-fatal SIPp TLS retry and watchdog notices from final stderr while retaining raw diagnostics.
- Request `--previous` pod logs only after Kubernetes reports a restart or terminated previous state.
- Collect PlaySBC/RTPengine logs from the exact profile start time and scope PlaySBC call-ID lines to the profile.
- Validate AKS LoadBalancer exposure before profile mutation and validate RTPengine advertised-IP alignment again after each profile rollout.
- Label the 200-path archive manifest as a preview and reconcile pre-manifest and final archive member counts.

## Compatibility

- The normal `kind-playsbc` active-active regression values are unchanged.
- AKS public SIP/RTP services, static IPs, real-device values, and 12-profile catalog are unchanged.
- Docker dual-realm, minikube compatibility, local SIPp, HA, observability, and AI/Rasa profile selection are unchanged.
- The local real-device profile rejects Azure exposure, active-active mode, blank/mismatched LAN addresses, multiple replicas, and RTP ranges outside `30000-30049`.

## Validation

- Complete repository gate passes: 320 tests with one expected platform skip.
- Default, active-active, AKS, and local real-device Helm renders remain isolated.
- Live `kind-playsbc` smoke passes `basic-signalling`, `rtpengine-media`, and `register-auth-tls`; every profile retained one merged PCAP and one `sipmsg.log`, with no split PCAP or final TLS/watchdog noise.
- The v2.5.1 AKS all-12 pass remains the cloud baseline; v2.5.2 requires the same AKS and existing local regression gates before production use.
