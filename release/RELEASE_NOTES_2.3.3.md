# PlaySBC v2.3.3

AKS regression auth isolation hotfix.

## Why

An AKS regression run after the real-device OBi1022/Zoiper lab failed because Helm `--reuse-values` carried `authSecret.enabled=true` from the live real-device deployment into profiles that intentionally exercise direct REGISTER/200 flows.

That caused open-registration profiles such as `registered-inbound`, `rtpengine-media`, `rtpengine-transcoding`, TCP/TLS media profiles, and `rtcp-receiver-quality` to receive `403 Forbidden` during SIPp B registration.

## What Changed

- The Kubernetes regression runner now renders auth-secret state per profile:
  - profiles with no `users` disable `authSecret` and run direct REGISTER/200;
  - digest-auth profiles enable a fresh profile-local auth secret;
  - inherited real-device `authSecret` and `existingSecret` values are not reused inside regression profiles.
- Added a regression test for the exact leak path: AKS real-device auth values must not break `registered-inbound`, while `register-auth-success` must still use digest credentials.
- Kept v2.3.2 image-publish fix and v2.3.1 AKS single-workload regression safety behavior.

## Validation

- `tests.test_mini_call_server` and `tests.test_sipp_harness` passed locally.
- `helm lint charts/playsbc` passed.
- `helm template playsbc charts/playsbc` rendered successfully.
- `mini_call_server.py`, `tools/run_k8s_regression.py`, `tools/run_k8s_regression_job.py`, `tools/run_b2bua_sipp_smoke.py`, and `tests/test_sipp_harness.py` compile cleanly.
- `git diff --check` passed.

## Operator Note

Use `v2.3.3` for the next AKS regression run after real-device lab testing. Real-device auth remains enabled when you deploy with the real-device Helm command; regression profiles now override auth mode only for the temporary profile rollout.
