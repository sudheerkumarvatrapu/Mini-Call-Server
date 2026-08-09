# PlaySBC v2.4.4

PlaySBC v2.4.4 is an RTCP evidence archive hotfix for the v2.4.x AKS real-device lab line.

## Highlights

- Added `rtpengine_explicit_rtcp` so RTPengine-backed real-device SDP explicitly advertises `a=rtcp:<RTP+1>` after plain RTP/AVP normalization removes `rtcp-mux`.
- Enabled explicit RTCP in the AKS real-device defaults, while keeping the general chart default off for existing kind/minikube regression behavior.
- Kept G.711-only, SIP-source-address NAT learning, media handover, and `NAT-wait` as the real-device baseline.
- Updated `tools/run_real_device_capture.py` to emit a downloadable evidence archive next to the capture folder.
- Kept the real-device lab artifact shape flat: one combined `capture.pcap`, `sipmsg.log`, PlaySBC/RTPengine logs, verdict logs, and `summary.log`.

## Validation Expectations

- Zoiper to OBi1022 and OBi1022 to Zoiper should keep two-way RTP through the Azure RTP LoadBalancer.
- Endpoint-facing SDP should include explicit RTCP targets on RTP+1 when `rtpengine_explicit_rtcp=true`.
- PCAP review should show SIP signalling, bidirectional RTP, and RTCP where endpoints emit RTCP.
- Real-device capture should print both the evidence folder path and the `.tgz` archive path.
