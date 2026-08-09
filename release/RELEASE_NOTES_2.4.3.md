# PlaySBC v2.4.3

PlaySBC v2.4.3 is a real-device evidence cleanup hotfix for the v2.4.x AKS lab line.

## Highlights

- Cleaned the default OBi1022/Zoiper AKS media baseline by leaving RTPengine `pierce NAT` disabled unless explicitly needed.
- Kept `NAT-wait`, SIP-source-address learning, and media handover enabled for normal home-NAT learning.
- Improved `tools/run_real_device_capture.py` so one `Ctrl-C` finalizes the evidence bundle instead of losing the combined `capture.pcap`.
- Added binary-safe fallback copying for the host-network capture pod when `kubectl cp` cannot stream the PCAP.
- Updated the AKS and real-device runbooks to explain pre-answer RTPengine pinhole packets versus real voice RTP.

## Validation Expectations

- Real voice RTP should appear after `200 OK` and ACK.
- If `pierce NAT` is re-enabled, small 12-byte RTPengine pinhole packets can appear after `180 Ringing`; those are not speech frames.
- Manual capture interruption should still produce `capture.pcap`, `sipmsg.log`, `playsbc.log`, `rtpengine.log`, and `summary.log`.
