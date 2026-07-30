# PlaySBC v1.6.2

Real-device AKS hotfix for OBi1022 to Zoiper calling through PlaySBC.

## Fixed

- Supports proxy-style hardphone INVITEs where the Request-URI is the SBC public IP and the dialed extension is carried in the `To` header.
- Prevents OBi/ATA calls such as `1001 -> 1002` from being routed as if the AKS public IP were the called user.
- Adds parser coverage for direct Request-URI calls and host-only proxy-style Request-URI calls.

## Notes

- `v1.6.1` added home-NAT registrar routing for private Contact addresses.
- `v1.6.2` completes the first real-device call path by fixing target selection for OBi-style outbound INVITEs.
- After upgrading AKS to `v1.6.2`, re-test `OBi1022 1001 -> Zoiper 1002`.

## Validation

- `python3 -m unittest tests.test_mini_call_server`
- `python3 -m py_compile mini_call_server.py`
- `git diff --check`
