# PlaySBC v2.2.0

AKS regression/runtime hardening release.

## Why

The Azure AKS regression suite can start while Azure is still allocating public LoadBalancer ingress. In that window, calls may be logically fine later, but the runner can report runtime/preflight errors because SIP or RTP public exposure was not fully ready when the test began.

## What Changed

- `--aks-profiles` now requires public SIP ingress by default.
- `--aks-profiles` now requires the public RTP LoadBalancer by default.
- The AKS wrapper waits for both SIP and RTP public LoadBalancer ingress before launching the in-cluster runner.
- AKS exposure validation now checks the public RTP service exposes UDP `30000-30049`.
- AKS preflight evidence clearly reports missing or pending `sip-public` and `rtp-public` services.
- The checked-in AKS values now use the same `30000-30049` lab RTP range as the Azure playbook.

## Validation

- Python compile check passed for the AKS runner modules and SIPp harness tests.
- Focused AKS harness tests passed:
  - AKS profile shortcut defaults
  - LoadBalancer wait until ingress readiness
  - Missing RTP public service detection

## Notes

This release does not claim the real-device OBi1022/Zoiper one-way RTP issue is fully solved. That media path remains the next hardening target.
