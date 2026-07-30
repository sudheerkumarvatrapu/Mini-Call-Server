# PlaySBC v1.6.3

Real-device AKS hotfix for OBi1022 and Zoiper B2BUA calling.

## Fixed

- Retries INVITE routing from the `To` header user when the Request-URI user is not routable.
- Handles hardphone/ATA INVITEs where the Request-URI contains the SBC public IP or another proxy-style user but the dialed extension is in `To`.
- Keeps in-dialog ACK/BYE destination on the learned registered target when the remote Contact is a private LAN address.
- Adds `rtpengine.advertisedIP` so Azure RTPengine can advertise the public RTP LoadBalancer IP in SDP for internet softphone/hardphone media.
- Adds unit coverage for real-device target fallback and private dialog Contact BYE routing.

## Notes

- This is a follow-up to `v1.6.2`; use `v1.6.3` for OBi1022 `1001` to Zoiper `1002` call testing.
- For internet media, set `rtpengine.advertisedIP` to the Azure RTP public IP and expose the configured RTP port range on the Azure RTP LoadBalancer.

## Validation

- `python3 -m unittest tests.test_mini_call_server`
- `python3 -m py_compile mini_call_server.py`
- `helm lint charts/playsbc`
- `git diff --check`
