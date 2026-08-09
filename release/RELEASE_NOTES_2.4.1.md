# PlaySBC v2.4.1

PlaySBC v2.4.1 is a real-device capture hotfix for the v2.4.x evidence line.

## Highlights

- Fixed manual OBi1022/Zoiper AKS PCAP capture when PlaySBC and RTPengine containers do not contain `tcpdump`.
- Replaced separate PlaySBC/RTPengine capture folders with one temporary host-network capture pod.
- Kept one flat Wireshark-ready `capture.pcap` containing SIP, RTP/RTCP, RTPengine control, and AKS LoadBalancer/NodePort networking evidence.
- Added capture-pod manifest, lifecycle logs, cluster snapshots, PlaySBC logs, RTPengine logs, `sipmsg.log`, and RTPengine packet verdicts in one evidence bundle.
- Updated AKS and real-device playbooks with capture image guidance and ACR fallback commands.

## Validation Expectations

- Manual real-device capture should create `logs/Real-Device-Lab/real-device-capture-*/capture.pcap`.
- No `capture-playsbc` or `capture-rtpengine` evidence subfolders should be produced.
- If a manual call fails, the same capture bundle should still contain SIP route failure evidence and cluster service/pod snapshots.
