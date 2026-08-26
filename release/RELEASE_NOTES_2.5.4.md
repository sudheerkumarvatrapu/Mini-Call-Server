# PlaySBC v2.5.4

PlaySBC v2.5.4 fixes single-node kind real-device upgrades that could wait until Helm's atomic timeout.

## Local Real-Device Lab

- Use Kubernetes `Recreate` strategy for the PlaySBC Deployment only when `localRealDevice.enabled=true` on `kind-playsbc-real-device`.
- Release SIP host ports `5061/5062` before scheduling the replacement pod.
- Keep the v2.5.3 optional-CA TLS startup correction.

## Evidence Hardening

- Preserve the existing combined PCAP, SIP ladder, RTP/RTCP verdict, and regression archive contracts.

## Compatibility

- Default, AKS, and non-local PlaySBC Deployments retain Kubernetes `RollingUpdate` behavior.
- Active-active StatefulSets, RTPengine, SIP routing, RTP/RTCP, regression profiles, observability, and AI Voice Gateway behavior are unchanged.

## Validation

- The complete repository test suite passes.
- The local real-device chart renders `strategy.type: Recreate`.
- Default and AKS chart renders do not contain the local-only strategy.
- The live v2.5.3 workload reached `1/1 Running` after confirming the original scheduler failure was exclusively a host-port conflict.
