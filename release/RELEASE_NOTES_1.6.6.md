# PlaySBC v1.6.6

Real-device AKS answer-window hotfix for OBi1022 and Zoiper calls.

## Fixed

- Adds `b2bua_invite_timeout` so real hardphones can ring long enough before PlaySBC returns `480 Temporarily Unavailable`.
- Keeps the default timeout at `10.0` seconds for fast SIPp/local/Kubernetes regression behavior.
- Documents the real-device AKS value as `playsbc.config.b2bua_invite_timeout=60.0`.
- Includes the uncommitted v1.6.5 lab cleanup:
  - Helm now defaults missing advertised SIP/B2BUA IPs to `$POD_IP` outside active-active mode too.
  - Helm enables `reject_unknown_routes=true` by default so missing registrar routes do not fall back to echo SDP.
  - The real-device runbook documents the Zoiper `Unparsable SDP` fallback-route symptom.

## Real Device Lab Notes

- If Zoiper receives `480 Temporarily Unavailable` after the OBi rings, check pod logs for `reason=outbound_invite_timeout`.
- Re-run the real-device Helm command with `b2bua_invite_timeout=60.0`, re-register both devices, place one call, and answer the hardphone inside that window.
- Use the current Azure SIP LoadBalancer IP from `kubectl` as `sip_advertised_ip` and `b2bua_advertised_ip`; do not hard-code an old public IP.

## Validation

- `python3 -m unittest tests.test_mini_call_server`
- `python3 -m py_compile mini_call_server.py`
- `helm lint charts/playsbc`
- `helm template charts/playsbc`
- `git diff --check`
