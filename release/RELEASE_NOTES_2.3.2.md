# PlaySBC v2.3.2

PlaySBC image publish hotfix.

## Why

The v2.3.1 tag included the AKS regression safety fix, but the `playsbc` container image publish failed while the RTPengine, SIPp, and regression-runner images succeeded. The PlaySBC image is the only image that downloads Piper/Vosk model assets during build, and its Piper voice download command used an obsolete `--download-dir` option.

## What Changed

- Updated `docker/playsbc.Dockerfile` to use Piper's current `download_voices --data-dir` CLI.
- Kept the v2.3.1 AKS regression safety behavior:
  - AKS readiness profiles default to one PlaySBC plus one RTPengine.
  - Local full K8s regression keeps active-active by default.
  - AKS active-active remains explicit with `--active-active-topology`.
- Added a Dockerfile regression test so the stale Piper flag does not come back.

## Validation

- `tests.test_sipp_harness` passed locally.
- `tests.test_mini_call_server` and `tests.test_sipp_harness` passed together during the v2.3.1 safety change.
- `helm lint charts/playsbc` and chart rendering passed during the v2.3.1 safety change.

## Operator Note

Use `v2.3.2` for AKS regression and real-device lab image imports. Do not use `v2.3.1` for the PlaySBC image because that tag was cut before this Dockerfile hotfix.
