# PlaySBC v2.4.2

PlaySBC v2.4.2 is a real-device registrar NAT hotfix for the v2.4.x AKS lab line.

## Highlights

- Fixed Zoiper -> OBi1022 inbound-call routing when the OBi Contact port and observed public REGISTER source port differ behind home NAT.
- Preserved Kubernetes/private same-host Contact-port behavior so local kind/minikube and AKS regression SIPp pods remain compatible.
- Added unit coverage for public NAT port remap routing.
- Kept the v2.4.1 single combined real-device `capture.pcap` evidence workflow unchanged.

## Validation Expectations

- OBi1022 `1001` should re-register first, then Zoiper `1002` -> OBi1022 `1001` should route to the observed public REGISTER source endpoint.
- OBi1022 `1001` -> Zoiper `1002` should remain two-way RTP green.
- Local/kind/minikube/AKS regression routing should not change for private pod registrations where Contact and source host match.
