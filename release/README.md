# PlaySBC Release Artifacts

This folder keeps local release notes and Helm chart packages for PlaySBC.

Current release:

- Version: `2.5.0`
- Helm chart package: `helm/playsbc-2.5.0.tgz`
- Project license: MIT
- Chart version: `2.5.0`
- Application version: `2.5.0`

Rebuild the Helm package with:

```bash
helm package charts/playsbc --destination release/helm
shasum -a 256 release/helm/playsbc-2.5.0.tgz > release/helm/playsbc-2.5.0.tgz.sha256
```

## Container Image Deployment

The `.tgz` chart package contains Kubernetes manifests and config, not image layers. End users deploy the chart and point it at PlaySBC and RTPengine container images.

Published GHCR images for this release:

- `ghcr.io/sudheerkumarvatrapu/playsbc:2.5.0`
- `ghcr.io/sudheerkumarvatrapu/playsbc-rtpengine:2.5.0`
- `ghcr.io/sudheerkumarvatrapu/playsbc-k8s-regression:2.5.0`
- `ghcr.io/sudheerkumarvatrapu/playsbc-sipp:2.5.0`

Deploy the release chart:

```bash
helm upgrade --install playsbc helm/playsbc-2.5.0.tgz \
  --namespace playsbc \
  --create-namespace \
  -f configs/kubernetes/active-active-values.yaml \
  --set image.repository=ghcr.io/sudheerkumarvatrapu/playsbc \
  --set-string image.tag=2.5.0 \
  --set rtpengine.enabled=true \
  --set rtpengine.image.repository=ghcr.io/sudheerkumarvatrapu/playsbc-rtpengine \
  --set-string rtpengine.image.tag=2.5.0 \
  --set rtpengine.hostNetwork=false
```

This is the normal Kubernetes shape for `v1.5.5` and later:

```text
PlaySBC StatefulSet replicas: 2
RTPengine StatefulSet replicas: 2
Prometheus Deployment replicas: 1
Grafana Deployment replicas: 1
```

If a deployment shows only one PlaySBC pod and one RTPengine pod, active-active values were not applied. Re-run Helm with `configs/kubernetes/active-active-values.yaml` or equivalent `--set topology.activeActive.enabled=true` values before running regression.

Kubernetes regression from published images:

```bash
PYTHONPYCACHEPREFIX=/private/tmp/playsbc-pycache python3 tools/run_k8s_regression_job.py \
  --all-profiles \
  --runner-image ghcr.io/sudheerkumarvatrapu/playsbc-k8s-regression:2.5.0 \
  --sipp-image ghcr.io/sudheerkumarvatrapu/playsbc-sipp:2.5.0 \
  --playsbc-image ghcr.io/sudheerkumarvatrapu/playsbc:2.5.0 \
  --set-playsbc-image \
  --no-load-playsbc-image \
  --no-load-sipp-image \
  --kind-cluster playsbc
```

Azure AKS profile runs write a verified evidence bundle automatically:

```text
logs/AKS-Regression/latest-aks-regression.tgz
```

They also wait for Azure LoadBalancer ingress before the regression Job starts. For AKS profile runs in v2.4.x and later, the wrapper keeps readiness profiles on a single PlaySBC/RTPengine workload by default, validates UDP media ports `30000-30049`, records RTPengine advertised-IP alignment evidence when RTPengine pods are present, and fails profiles with stale or ambiguous SIP/RTP/SRTP evidence.

Historical release notes are kept as `RELEASE_NOTES_<version>.md`.

## Release Documentation Gate

Every version bump must update the current version and runnable commands in `README.md`, `docs/KUBERNETES_LOCAL.md`, `docs/KUBERNETES_HELM_RUNBOOK.md`, `docs/AZURE_AKS.md`, and `docs/REAL_DEVICE_LAB.md`. The release is not documentation-complete until local kind/minikube, AKS, and real-device playbooks all point to the same version.
