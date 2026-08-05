# PlaySBC v2.3.0

Real-device AKS NAT pinhole hardening for OBi1022 and Zoiper calls through RTPengine.

## Why

The v2.2.2 AKS real-device run proved SIP routing and RTPengine anchoring were active. RTPengine saw packets in both directions, but one-way audio could still appear with home-NAT endpoints because a phone may not accept far-end RTP until its local NAT pinhole is open.

## What Changed

- Added `playsbc.config.rtpengine_nat_wait`.
- Added `playsbc.config.rtpengine_pierce_nat`.
- Passed both controls to RTPengine offer and answer as `NAT-wait` and `pierce NAT`.
- Added `RTPENGINE NAT PINHOLE` evidence logs for offer/answer.
- Enabled both flags in the AKS real-device values file.
- Updated the real-device and AKS playbooks with the new baseline.

## AKS Real-Device Baseline

Keep the v2.2.2 public SIP/RTP LoadBalancer settings and add:

```bash
--set playsbc.config.rtpengine_nat_wait=true \
--set playsbc.config.rtpengine_pierce_nat=true
```

The generic chart defaults remain `false`, so local and Kubernetes regression behavior only changes when a profile or deployment explicitly enables these flags.

## Validation

- RTPengine NG flag encoding covers `SIP source address`, `media handover`, `NAT-wait`, and `pierce NAT`.
- PlaySBC config loading preserves the new boolean controls.
- Kubernetes profile rendering carries the flags into the generated PlaySBC config.
