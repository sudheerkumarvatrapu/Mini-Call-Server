# PlaySBC v2.6.0

PlaySBC v2.6.0 is the final public MIT feature gate. It closes the public line with stronger long-run stability, explicit two-leg packet evidence, and one 70-profile compatibility catalog shared by Docker, kind, AKS, HA, AI, and real-device lanes.

## Regression Stability

- The full catalog now contains 70 profiles.
- `evidence-b2bua-two-leg-pcap` proves a bridged call has core and peer packet sources plus two distinct B2BUA INVITE Call-IDs.
- The launcher reports `Regression progress: X/70` while a Kubernetes Job is running.
- Local macOS runs start a scoped `caffeinate` process so host sleep cannot create false SIPp timeouts during long soak and load profiles.
- The three load failures in `k8s-regression-20260827-201206` were traced to host suspension; caller SIPp had completed its workload before the delayed peer timeout.

## Evidence Hardening

- Combined captures are validated before per-role source files are removed.
- `pcap-legs.json` records expected roles, per-role packet counts, merged packet count, SIP event count, distinct INVITE Call-IDs, and the final evidence verdict.
- Plain SIP profiles with bridged core and peer roles require at least two distinct INVITE legs.
- Missing or empty expected role captures now fail evidence collection instead of producing a misleading merged PCAP.
- High-volume profiles that intentionally omit packet capture remain explicitly identified as compact evidence profiles.

## Local Real-Device Lab

- The isolated `kind-playsbc-real-device` lane remains available for OBi1022 and Zoiper registration, calls, RTP/RTCP, and capture without changing the AKS or full-regression topology.
- Current values and runbooks consistently select v2.6.0 images for PlaySBC and RTPengine.

## Product Documentation

- The public evolution plan is frozen at the v2.6.0 baseline and no longer carries future product roadmap commitments.
- `PlaySBC-v2.6.0-Product-Guide.pdf` provides one branded feature, architecture, and administration guide for Docker, kind, minikube, Azure AKS, Helm, observability, evidence, and real-device labs.
- The guide cover identifies Sudheer Kumar Vatrapu as contributor and clearly distinguishes the engineering lab from a production-certified SBC.

## Compatibility

- Existing SIP, RTPengine, AI, RFC 5359 hold/resume, HA, observability, and real-device behavior is unchanged by the sleep-inhibition and evidence-certification work.
- The standard `kind-playsbc` active-active lane and Azure AKS deployment retain separate values and networking contracts.
- The PlaySBC image retries rate-limited Piper voice downloads and verifies both pinned model files before completing the build.
- The release gate includes unit checks, Helm lint/render checks, Docker image publication, and operator-run Kubernetes regression.

## Public And Commercial Boundary

- Source, charts, images, and artifacts published through v2.6.0 remain under their published MIT terms.
- The exact v2.6.0 tag and tree are the provenance baseline for the access-controlled `SBC-Comm` repository.
- Production Voice AI and Enterprise SBC development after that fork is private commercial work. The first packaged commercial release is targeted at v6.0.0 and remains subject to legal and third-party review.

## Operator Acceptance

The repository validation performed for this release does not replace the environment-specific regression gate. Run the 70-profile local kind catalog and the applicable AKS and real-device lanes before promoting the images in a deployment.
