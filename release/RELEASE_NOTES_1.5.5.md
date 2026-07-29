# PlaySBC v1.5.5

PlaySBC `v1.5.5` is an Azure AKS readiness and evidence hardening hotfix.

## What Changed

- `tools/run_k8s_regression_job.py` now creates `latest-aks-regression.tgz` automatically for `--aks-profiles` runs.
- AKS profile runs now wait for selected Azure `LoadBalancer` services to receive ingress before the regression Job starts.
- The default AKS LoadBalancer wait is 20 minutes, with `--aks-load-balancer-wait-timeout` and `--aks-load-balancer-poll-interval` overrides.
- The archive is verified by reopening it and counting real file members before the runner prints the download path.
- Each AKS run folder now includes `archive-manifest.txt` with the source run, archive path, and captured files.
- The Azure guide now tells users to download the runner-generated `.tgz` and validate it with `tar -tzf`.
- The guide removes the manual tar step that could create a tiny empty archive when `$RUN` was unset.

## Why

The pasted AKS run started while Azure SIP/RTP public services still showed `EXTERNAL-IP <pending>`, then the strict public-ingress validation failed inside the suite. A later manual packaging command also produced an empty downloaded archive because `$RUN` was unset. This hotfix waits for Azure ingress before testing and makes the evidence bundle deterministic.

## Runtime Scope

No SIP, RTP, RTPengine, Helm service, or regression profile behavior changed. This release hardens the AKS launch wrapper, Azure readiness documentation, and evidence collection.

## Artifacts

- Helm chart: `playsbc-1.5.5.tgz`
- PlaySBC image: `ghcr.io/sudheerkumarvatrapu/playsbc:1.5.5`
- RTPengine image: `ghcr.io/sudheerkumarvatrapu/playsbc-rtpengine:1.5.5`
- Regression runner image: `ghcr.io/sudheerkumarvatrapu/playsbc-k8s-regression:1.5.5`
- SIPp image: `ghcr.io/sudheerkumarvatrapu/playsbc-sipp:1.5.5`

## Validation

- Unit test for verified AKS archive generation.
- Unit test for AKS LoadBalancer wait polling.
- Unit test proving Kubernetes Job dry-run does not mutate Helm or cluster state.
- Python compile check for the Kubernetes regression job wrapper.
- Helm chart lint.
- Helm template render with AKS values.
