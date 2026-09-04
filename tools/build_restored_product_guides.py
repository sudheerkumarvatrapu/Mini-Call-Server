#!/usr/bin/env python3
"""Restore validated runbooks from v2.5.4 for the v2.6.0 public guides."""

from __future__ import annotations

import subprocess
from pathlib import Path

from build_product_guide_html import build as build_html
from build_product_guide_pdf import build as build_pdf


ROOT = Path(__file__).resolve().parents[1]
REFERENCE_TAG = "v2.5.4"
VERSION = "2.6.0"
SOURCE = ROOT / "docs" / "PRODUCT_GUIDE.md"
PDF = ROOT / "output" / "pdf" / "PlaySBC-v2.6.0-Product-Guide.pdf"
HTML = ROOT / "output" / "html" / "PlaySBC-v2.6.0-Product-Guide.html"

RUNBOOKS = (
    "AI_VOICE_GATEWAY.md",
    "AZURE_AKS.md",
    "EVOLUTION_PLAN.md",
    "KUBERNETES_HELM_RUNBOOK.md",
    "KUBERNETES_LOCAL.md",
    "OBSERVABILITY.md",
    "README.md",
    "REAL_DEVICE_LAB.md",
    "RTPENGINE_LOCAL.md",
)


def tagged(path: str) -> str:
    return subprocess.check_output(
        ["git", "show", f"{REFERENCE_TAG}:{path}"], cwd=ROOT, text=True
    )


def main() -> int:
    recovered: list[tuple[str, str]] = []
    for name in RUNBOOKS:
        content = tagged(f"docs/{name}").replace("2.5.4", VERSION)
        (ROOT / "docs" / name).write_text(content, encoding="utf-8")
        recovered.append((name, content))

    prefix = """# PlaySBC v2.6.0 Product Guide

Validated Deployment, Administration, and Troubleshooting Runbooks

Contributor: Sudheer Kumar Vatrapu

Status: Validated v2.6.0 deployment and administration commands

# Document Control

| Field | Value |
| --- | --- |
| Product | PlaySBC |
| Release | v2.6.0 |
| Command baseline | Restored canonical AKS, Kubernetes, real-device, media, and operations runbooks |
| AKS topology | One PlaySBC pod and one RTPengine pod by default |
| Command policy | Command blocks are reproduced verbatim from the tagged Markdown runbooks |

## Using This Guide

The browser edition provides working COPY buttons. PDF viewers keep command text selectable but cannot write to the clipboard. Each chapter below identifies its original tagged Markdown source.

## Opening Regression Evidence

Every generated regression report now packages its linked artifacts in an
`evidence/` directory beside `latest.html`. Keep the complete report directory
together when moving or archiving results; copying `latest.html` alone breaks
its relative links.

- Text evidence such as SIP traces, workload logs, Kubernetes snapshots,
  values YAML, and JSON opens in a browser-safe HTML viewer.
- Each viewer provides **Back to report** and **Download raw file** actions.
- Packet captures and other binary evidence open a metadata page with a raw
  download action for Wireshark or the appropriate desktop application.
- Embedded or linked WAV evidence remains available from AI speech reports.
- A separate localhost server is no longer required for normal viewing. The
  `tools/serve_regression_report.py` command remains available as an optional
  presentation mode.

Open a copied Kubernetes regression report directly on macOS:

```bash
open "/absolute/path/to/k8s-reports/latest.html"
```

For the links to remain portable, preserve this structure:

```text
k8s-reports/
|-- latest.html
|-- <run-id>.html
|-- <run-id>.json
`-- evidence/
    `-- <profile>/
        |-- log.sip
        |-- log.sip.html
        |-- capture.pcap
        `-- capture.pcap.html
```
"""
    chapters = [prefix]
    for name, content in recovered:
        chapters.append(f"\n# Restored Runbook: docs/{name}\n\n{content.rstrip()}\n")
    chapters.append(
        r'''
# AKS Complete Cleanup - One Command

Use this when the entire PlaySBC Azure lab must be removed before a fresh start. It deletes `playsbc-aks-rg` and `playsbc-network-rg`, waits for both asynchronous deletions, and then removes the stale kubeconfig entries. The AKS-managed `MC_*` resource group is removed with the AKS resource group; do not delete it separately.

```bash
bash -lc '
set -euo pipefail

AKS_RG=playsbc-aks-rg
NETWORK_RG=playsbc-network-rg
AKS_NAME=playsbc-aks
SUB_ID=$(az account show --query id -o tsv)
: "${SUB_ID:?No active Azure subscription}"

az account show \
  --query "{Subscription:name,ID:id,Tenant:tenantId}" \
  -o table

az group list \
  --subscription "$SUB_ID" \
  --query "[?name==\`$AKS_RG\` || name==\`$NETWORK_RG\`].{Name:name,Location:location,State:properties.provisioningState}" \
  -o table

read -r -p "Type DELETE to permanently remove all PlaySBC Azure resources: " CONFIRM
[ "$CONFIRM" = DELETE ] || { echo "Cancelled."; exit 1; }

pkill -INT -f "helm upgrade.*playsbc" 2>/dev/null || true

for RG in "$AKS_RG" "$NETWORK_RG"; do
  if [ "$(az group exists --subscription "$SUB_ID" --name "$RG")" = true ]; then
    az group delete \
      --subscription "$SUB_ID" \
      --name "$RG" \
      --yes \
      --no-wait
  fi
done

while true; do
  A=$(az group exists --subscription "$SUB_ID" --name "$AKS_RG")
  N=$(az group exists --subscription "$SUB_ID" --name "$NETWORK_RG")
  echo "$(date)  $AKS_RG=$A  $NETWORK_RG=$N"
  [ "$A" = false ] && [ "$N" = false ] && break
  sleep 30
done

kubectl config delete-context "$AKS_NAME" 2>/dev/null || true
kubectl config delete-cluster "$AKS_NAME" 2>/dev/null || true
kubectl config unset "users.clusterUser_${AKS_RG}_${AKS_NAME}" 2>/dev/null || true

echo "All PlaySBC Azure resources deleted."
'
```
'''
    )
    SOURCE.write_text("\n".join(chapters), encoding="utf-8")

    build_pdf(SOURCE, PDF, VERSION)
    build_html(SOURCE, HTML, VERSION)
    print(PDF)
    print(HTML)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
