# PlaySBC v1.6.0

PlaySBC `v1.6.0` is an AKS evidence correctness release.

## What Changed

- AKS combined `capture.pcap` is now timestamp-sorted across core and peer capture agents instead of appending one capture file after the other.
- AKS packet capture now filters to SIP, RTP/SRTP, and RTCP lab ports, removing DNS and unrelated Kubernetes pod noise from Wireshark review.
- AKS OPTIONS keepalive reports now render an OPTIONS-only ladder instead of a generic B2BUA INVITE ladder.
- The Azure AKS playbook now has a dedicated evidence review section explaining `log.sip`, `log.media`, `log.transcoding`, `log.platform`, `capture.pcap`, and the runner-generated archive.
- Chart and reference image tags move to `1.6.0`.

## Why

The Azure AKS regression profiles were passing, but some evidence was confusing:

- `esbc-options-keepalive` could show a generic call ladder even though the actual SIP trace was only `OPTIONS -> 200 OK`.
- The merged AKS `capture.pcap` could display messages out of order because core and peer captures were concatenated instead of merged by packet timestamp.
- Broad `udp or tcp` capture included DNS/background traffic, making the PCAP harder to review.

This release fixes those evidence issues so AKS logs, ladders, and PCAPs are cleaner for SIP/RTP review.

## Runtime Scope

No SIP routing, RTPengine call setup, media negotiation, or Azure LoadBalancer behavior changed. This is a regression evidence, report, capture, and documentation release.

## Artifacts

- Helm chart: `playsbc-1.6.0.tgz`
- PlaySBC image: `ghcr.io/sudheerkumarvatrapu/playsbc:1.6.0`
- RTPengine image: `ghcr.io/sudheerkumarvatrapu/playsbc-rtpengine:1.6.0`
- Regression runner image: `ghcr.io/sudheerkumarvatrapu/playsbc-k8s-regression:1.6.0`
- SIPp image: `ghcr.io/sudheerkumarvatrapu/playsbc-sipp:1.6.0`

## Validation

- Unit test for timestamp-sorted AKS PCAP merge.
- Unit test for focused AKS capture filter.
- Unit test for OPTIONS-only AKS ladder rendering.
- Python compile check for the Kubernetes regression runner and test harness.
- Helm chart lint.
- Helm template render with AKS values.
