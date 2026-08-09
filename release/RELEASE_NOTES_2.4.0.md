# PlaySBC v2.4.0

PlaySBC v2.4.0 is the regression and real-device evidence hardening milestone.

## Highlights

- Added strict Kubernetes evidence validation for SRTP/RTPengine profiles.
- Kept OPTIONS keepalive evidence isolated from INVITE, Rasa, and unrelated profile traffic.
- Preserved lean regression artifacts: one merged `capture.pcap` and one root `sipmsg.log` per profile.
- Added `tools/run_real_device_capture.py` for OBi1022/Zoiper AKS lab captures with merged SIP/RTP/RTCP PCAP, SIP log, RTPengine log, and packet verdict evidence.
- Tolerated duplicate B2BUA BYE after recent call finalization with `200 OK` while keeping normal unknown-dialog failures intact.
- Updated AKS and real-device playbooks for v2.4.0 validation gates.

## Validation Expectations

- AKS regression profiles must pass strict evidence validation.
- SRTP profiles must prove RTPengine media-security handling and both RTP directions.
- Real-device OBi1022 and Zoiper calls should be tested in both directions with audible two-way RTP and `caller_to_callee=observed callee_to_caller=observed`.
- Local kind/minikube, Docker dual-realm, AKS, AI/Rasa, and manual SIPp workflows must remain compatible with this release line.
