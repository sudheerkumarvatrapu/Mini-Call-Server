# PlaySBC v1.6.4

Real-device B2BUA hotfix for OBi1022 and Zoiper calling through AKS.

## Fixed

- Uses candidate-based INVITE target routing across Request-URI and `To` header users.
- Prefers the `To` header when the Request-URI user looks like a proxy host or IP address.
- Logs INVITE route candidates, selected route, and route failures for real-device troubleshooting.
- Forwards BYE from either B2BUA leg, so a callee-side hangup can clear the caller side.
- Keeps inbound BYE destination on the learned INVITE source when the caller Contact is a private LAN address.

## Media

- Keeps the `rtpengine.advertisedIP` support from `v1.6.3`; set it to the Azure RTP public IP for internet RTP.

## Validation

- `python3 -m unittest tests.test_mini_call_server`
- `python3 -m py_compile mini_call_server.py`
- `helm lint charts/playsbc`
- `git diff --check`
