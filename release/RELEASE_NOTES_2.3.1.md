# PlaySBC v2.3.1

AKS regression safety hotfix.

## Why

The v2.3.0 real-device work kept media hardening intact, but an AKS readiness regression run exposed a bad default: `--aks-profiles` could run through active-active StatefulSets. Those readiness profiles are meant to validate Azure SIP/RTP LoadBalancer exposure, REGISTER, routing, RTPengine media, TLS/SRTP, and RTCP with a stable one-pod baseline. Running them through active-active can split REGISTER and INVITE across nodes before HA shared-state behavior is the test target.

## What Changed

- `--aks-profiles` now defaults to single-workload topology.
- Local full Kubernetes regression still defaults to active-active topology.
- Explicit `--active-active-topology` still works for AKS HA experiments.
- Single-workload profile rendering now actively disables stale `topology.activeActive` Helm values.
- The regression Job wrapper also sets `replicaCount=1`, `rtpengine.replicas=1`, and deletes stale active-active StatefulSets when single-workload mode is selected.
- Helm restore now waits on the workload kind represented by the restored values.
- Tests pin AKS readiness defaults, explicit AKS active-active opt-in, stale Helm value cleanup, combined PCAP retention, and root `sipmsg.log` evidence.

## Operator Rule

Use `--aks-profiles` for Azure readiness. Use `--active-active-topology` only when the purpose of the run is HA behavior.
