# Kubernetes Lab

The Helm chart deploys PlaySBC with HTTP liveness/readiness probes, optional Secret-backed SIP users, ClientIP dialog affinity, active-active StatefulSet lab mode, shared HA state, and paired RTPengine pods. The standard Kubernetes regression path now uses active-active PlaySBC plus active-active RTPengine by default, with logical core/peer realms; real secondary interfaces need Multus.

Expected standard lab shape:

```text
playsbc-playsbc-0
playsbc-playsbc-1
playsbc-playsbc-rtpengine-0
playsbc-playsbc-rtpengine-1
```

Always include `configs/kubernetes/active-active-values.yaml` for normal lab and regression runs. In single-node kind, this file keeps RTPengine on pod networking with `rtpengine.hostNetwork=false`, avoiding host-port collisions between RTPengine replicas.

## v2.5.0 Released-Image Lab

This is the standard local kind upgrade and full-regression procedure. It keeps PlaySBC, paired RTPengine replicas, Prometheus, and Grafana on the same release workflow.

```bash
cd /Users/sudheerkumar/Documents/Codex/2026-05-18/Mini-Call-Server

export PLAYSBC_VERSION=2.5.0

kubectl config use-context kind-playsbc
kubectl config set-context --current --namespace=playsbc

helm upgrade --install playsbc \
  "https://github.com/sudheerkumarvatrapu/PlaySBC/releases/download/v${PLAYSBC_VERSION}/playsbc-${PLAYSBC_VERSION}.tgz" \
  --namespace playsbc \
  --create-namespace \
  -f configs/kubernetes/active-active-values.yaml \
  --set image.repository=ghcr.io/sudheerkumarvatrapu/playsbc \
  --set-string image.tag="$PLAYSBC_VERSION" \
  --set image.pullPolicy=Always \
  --set rtpengine.enabled=true \
  --set rtpengine.image.repository=ghcr.io/sudheerkumarvatrapu/playsbc-rtpengine \
  --set-string rtpengine.image.tag="$PLAYSBC_VERSION" \
  --set rtpengine.image.pullPolicy=Always \
  --set rtpengine.hostNetwork=false \
  --set playsbc.config.media_backend=rtpengine \
  --set-string playsbc.config.rtpengine_url=udp://playsbc-playsbc-rtpengine:2223 \
  --set observability.enabled=true \
  --set observability.prometheus.retention=31d \
  --set observability.prometheus.persistence.size=5Gi \
  --set observability.grafana.persistence.size=2Gi

kubectl -n playsbc rollout status statefulset/playsbc-playsbc --timeout=180s
kubectl -n playsbc rollout status statefulset/playsbc-playsbc-rtpengine --timeout=180s
kubectl -n playsbc rollout status deployment/playsbc-playsbc-prometheus --timeout=180s
kubectl -n playsbc rollout status deployment/playsbc-playsbc-grafana --timeout=180s
kubectl -n playsbc get pods -o wide
kubectl -n playsbc get statefulsets

PYTHONPYCACHEPREFIX=/private/tmp/playsbc-pycache python3 tools/run_k8s_regression_job.py \
  --all-profiles \
  --runner-image "ghcr.io/sudheerkumarvatrapu/playsbc-k8s-regression:${PLAYSBC_VERSION}" \
  --sipp-image "ghcr.io/sudheerkumarvatrapu/playsbc-sipp:${PLAYSBC_VERSION}" \
  --playsbc-image "ghcr.io/sudheerkumarvatrapu/playsbc:${PLAYSBC_VERSION}" \
  --rtpengine-image "ghcr.io/sudheerkumarvatrapu/playsbc-rtpengine:${PLAYSBC_VERSION}" \
  --set-playsbc-image \
  --set-rtpengine-image \
  --no-load-playsbc-image \
  --no-load-rtpengine-image \
  --no-load-sipp-image \
  --kind-cluster playsbc
```

The rollout commands verify all four continuously running components before regression begins. The regression runner temporarily creates its own runner and core/peer SIPp pods; those pods disappear as each profile completes.

Optional observability access:

```bash
kubectl -n playsbc port-forward svc/playsbc-playsbc-grafana 3000:3000
kubectl -n playsbc port-forward svc/playsbc-playsbc-prometheus 9090:9090
```

Open Grafana at `http://127.0.0.1:3000` and Prometheus at `http://127.0.0.1:9090`.

## Release Maintenance Rule

Every PlaySBC release must update the `PLAYSBC_VERSION` value in this playbook before the release is considered complete. The same release change must keep `README.md`, `docs/KUBERNETES_HELM_RUNBOOK.md`, `docs/AZURE_AKS.md`, `docs/REAL_DEVICE_LAB.md`, chart metadata, image examples, and release notes aligned. Local kind/minikube regression remains a required compatibility gate for every minor or major change.

## Build Current Source In kind

```bash
kind create cluster --name playsbc
docker build -f docker/playsbc.Dockerfile -t playsbc:local .
docker build -f docker/rtpengine.Dockerfile -t playsbc/rtpengine:local .
kind load docker-image playsbc:local playsbc/rtpengine:local --name playsbc
helm upgrade --install playsbc charts/playsbc \
  -f configs/kubernetes/kind-values.yaml \
  -f configs/kubernetes/active-active-values.yaml
kubectl rollout status statefulset/playsbc-playsbc
kubectl rollout status statefulset/playsbc-playsbc-rtpengine
kubectl get pods,services
kubectl port-forward service/playsbc-playsbc 8080:8080 5060:5062
```

Check `http://127.0.0.1:8080/readyz` and `http://127.0.0.1:8080/metrics`. UDP SIP and RTP are easiest to test inside the kind network; TCP SIP can use the port-forward above.

## minikube

```bash
minikube start
eval $(minikube docker-env)
docker build -f docker/playsbc.Dockerfile -t playsbc:local .
docker build -f docker/rtpengine.Dockerfile -t playsbc/rtpengine:local .
helm upgrade --install playsbc charts/playsbc \
  -f configs/kubernetes/minikube-values.yaml \
  -f configs/kubernetes/active-active-values.yaml
kubectl rollout status statefulset/playsbc-playsbc
kubectl rollout status statefulset/playsbc-playsbc-rtpengine
minikube service playsbc-playsbc --url
```

Keep real credentials in a private values file or pre-create a Secret and set `authSecret.existingSecret`. Do not commit production passwords.

## Dialog Affinity Experiment

```bash
helm upgrade playsbc charts/playsbc \
  -f configs/kubernetes/kind-values.yaml \
  -f configs/kubernetes/dialog-affinity-values.yaml
kubectl scale deployment/playsbc-playsbc --replicas=2
kubectl get pods -l app.kubernetes.io/name=playsbc -o wide
```

This is a simple Deployment-only experiment. The normal HA lab mode uses `configs/kubernetes/active-active-values.yaml`, stable StatefulSet pod identities, SQLite-backed shared registrar/dialog state, node-to-RTPengine pairing, external-LB policy metadata, and per-node draining. It is still a lab store; PostgreSQL or Redis is a later hardening phase.

## Media Model

SIP reaches the PlaySBC Service. PlaySBC sends RTPengine NG control to the chart-managed RTPengine Service or to a stable paired RTPengine headless-service endpoint. In active-active regression, RTPengine uses pod networking to avoid host-port collisions in kind. Multus is the future path for real core and peer media interfaces inside Kubernetes.
