# PlaySBC Real Device Lab

Use this runbook for the first AKS test with one hardphone and one softphone.

```text
OBi1022 1001 -> Internet/NAT -> Azure LB UDP 5062 -> PlaySBC -> RTPengine -> Zoiper 1002
```

## 1. Upgrade AKS For Real Devices

Run in Azure Cloud Shell after the `v2.4.0` release/images are published.

```bash
export PLAYSBC_VERSION=2.4.0
export AKS_RG=playsbc-aks-rg
export NETWORK_RG=playsbc-network-rg
export AKS_NAME=playsbc-aks
export SIP_PIP_NAME=playsbc-sip-pip
export RTP_PIP_NAME=playsbc-rtp-pip
export ACR_NAME=$(az acr list --resource-group "$AKS_RG" --query "[0].name" -o tsv)
export NODE_RG=$(az aks show --resource-group "$AKS_RG" --name "$AKS_NAME" --query nodeResourceGroup -o tsv)
export SIP_PUBLIC_IP=$(az network public-ip show --resource-group "$NETWORK_RG" --name "$SIP_PIP_NAME" --query ipAddress -o tsv)
export RTP_PUBLIC_IP=$(az network public-ip show --resource-group "$NETWORK_RG" --name "$RTP_PIP_NAME" --query ipAddress -o tsv)

az acr import --name "$ACR_NAME" --source ghcr.io/sudheerkumarvatrapu/playsbc:$PLAYSBC_VERSION --image playsbc:$PLAYSBC_VERSION --force
az acr import --name "$ACR_NAME" --source ghcr.io/sudheerkumarvatrapu/playsbc-rtpengine:$PLAYSBC_VERSION --image playsbc-rtpengine:$PLAYSBC_VERSION --force
```

If ACR import returns `MANIFEST_UNKNOWN`, GHCR has not exposed the new image yet. From the repo on the Mac, watch the image build:

```bash
gh run list --workflow="container-images.yml" --limit 5
gh workflow run container-images.yml --ref v$PLAYSBC_VERSION
gh run watch <run-id> --exit-status
```

Then rerun the failed `az acr import`.

Deploy or upgrade AKS:

```bash
helm upgrade --install playsbc \
  https://github.com/sudheerkumarvatrapu/PlaySBC/releases/download/v$PLAYSBC_VERSION/playsbc-$PLAYSBC_VERSION.tgz \
  --namespace playsbc \
  --reuse-values \
  --set cloud.provider=azure \
  --set cloud.azure.enabled=true \
  --set cloud.azure.nodeResourceGroup="$NODE_RG" \
  --set cloud.azure.sip.public.enabled=true \
  --set cloud.azure.sip.public.publicIPResourceGroup="$NETWORK_RG" \
  --set cloud.azure.sip.public.publicIPName="$SIP_PIP_NAME" \
  --set cloud.azure.media.public.enabled=true \
  --set cloud.azure.media.public.publicIPResourceGroup="$NETWORK_RG" \
  --set cloud.azure.media.public.publicIPName="$RTP_PIP_NAME" \
  --set cloud.azure.media.public.portRange.enabled=true \
  --set cloud.azure.media.public.portRange.min=30000 \
  --set cloud.azure.media.public.portRange.max=30049 \
  --set image.repository="$ACR_NAME.azurecr.io/playsbc" \
  --set-string image.tag="$PLAYSBC_VERSION" \
  --set image.pullPolicy=Always \
  --set rtpengine.enabled=true \
  --set rtpengine.image.repository="$ACR_NAME.azurecr.io/playsbc-rtpengine" \
  --set-string rtpengine.image.tag="$PLAYSBC_VERSION" \
  --set rtpengine.image.pullPolicy=Always \
  --set rtpengine.rtpMin=30000 \
  --set rtpengine.rtpMax=30049 \
  --set-string rtpengine.advertisedIP="$RTP_PUBLIC_IP" \
  --set playsbc.config.media_backend=rtpengine \
  --set-string playsbc.config.rtpengine_url=udp://playsbc-playsbc-rtpengine:2223 \
  --set playsbc.config.reject_unknown_routes=true \
  --set playsbc.config.b2bua_invite_timeout=60.0 \
  --set playsbc.config.rtpengine_g711_only=true \
  --set playsbc.config.rtpengine_plain_rtp_sdp=true \
  --set playsbc.config.rtpengine_sip_source_address=true \
  --set playsbc.config.rtpengine_media_handover=true \
  --set playsbc.config.rtpengine_nat_wait=true \
  --set playsbc.config.rtpengine_pierce_nat=true \
  --set-string playsbc.config.sip_advertised_ip="$SIP_PUBLIC_IP" \
  --set-string playsbc.config.b2bua_advertised_ip="$SIP_PUBLIC_IP" \
  --set authSecret.enabled=true \
  --set-string authSecret.users.1001=secret-password \
  --set-string authSecret.users.1002=secret-password

kubectl -n playsbc rollout restart deployment/playsbc-playsbc deployment/playsbc-playsbc-rtpengine
kubectl -n playsbc rollout status deployment/playsbc-playsbc --timeout=180s
kubectl -n playsbc rollout status deployment/playsbc-playsbc-rtpengine --timeout=180s
```

Hard preflight:

```bash
kubectl -n playsbc get svc playsbc-playsbc-azure-sip-public playsbc-playsbc-azure-rtp-public -o wide
kubectl -n playsbc get pod -l app.kubernetes.io/name=playsbc-rtpengine -o jsonpath='{.items[0].spec.containers[0].args}{"\n"}'
```

The SIP service must show the SIP public IP, the RTP service must show the RTP public IP, and the RTPengine command must include `!$RTP_PUBLIC_IP` with ports `30000-30049`.

## 2. Configure OBi1022 As `1001`

Open `http://192.168.1.9`, then disable old provider provisioning:

```text
System Management -> Auto Provisioning
OBiTALK Provisioning: Disabled
ITSP Provisioning: Disabled
Firmware Update: Manual or Disabled
```

Configure SP1:

```text
Service Providers -> ITSP Profile A -> SIP
ProxyServer: <SIP_PUBLIC_IP>
ProxyServerPort: 5062
ProxyServerTransport: UDP
RegistrarServer: <SIP_PUBLIC_IP>
RegistrarServerPort: 5062
OutboundProxy: blank
X_DnsSrv: false
X_UseTokenAuth: false
X_DiscoverPublicAddress: true
X_UsePublicAddressInVia: true
X_UseRport: true

Voice Services -> SP1 Service
Enable: checked
X_ServProvProfile: A
AuthUserName: 1001
AuthPassword: secret-password
URI: 1001
X_DisplayLabel: 1001
X_DisplayNumber: 1001
RegisterEnable: checked
KeepAliveEnable: checked

Service Providers -> ITSP Profile A -> RTP
X_RTPTransport: UDP
```

## 3. Configure Zoiper As `1002`

```text
Username: 1002
Password: secret-password
Domain / Host: <SIP_PUBLIC_IP>:5062
Transport: UDP
Outbound proxy: blank
```

## 4. Monitor Registration

```bash
kubectl -n playsbc logs deployment/playsbc-playsbc -f --since=10m \
  | grep -aE "REGISTER|Registered|401|403|1001|1002"
```

Expected registration:

```text
Challenged REGISTER for 1001
Registered 1001 -> sip:1001@...
Challenged REGISTER for 1002
Registered 1002 -> sip:1002@...
```

## 5. Monitor Calls And RTP

Use this command while placing calls. It intentionally omits REGISTER noise so signalling and media evidence are readable.

```bash
kubectl -n playsbc logs deployment/playsbc-playsbc -f --since=10m \
  | grep -aE "SIP (INVITE|ACK|BYE|CANCEL)|SIP TX response|SIP response|INVITE ROUTE|ROUTE FAILED|B2BUA|SDP SUMMARY|RTPENGINE PORT ALLOCATION|RTPENGINE NAT LEARNING|RTPENGINE NAT PINHOLE|RTPENGINE PACKET VERDICT|RTPengine"
```

Expected call tests:

```text
OBi1022 1001 -> Zoiper 1002
Zoiper 1002 -> OBi1022 1001
```

The OBi can register with a private Contact such as `192.168.1.9:5060`. PlaySBC keeps that Contact in SIP, but sends packets to the observed public REGISTER source so AKS can reach the device through NAT.

Good call evidence:

- `INVITE ROUTE SELECTED` routes to the registered peer.
- `RTPENGINE MEDIA SECURITY` shows `RTP/AVP`, `ice=remove`, `sip_source_address=true`, `media_handover=true`, `nat_wait=true`, and `pierce_nat=true`.
- `SDP SUMMARY` shows public RTP media on the Azure RTP LoadBalancer IP and ports inside `30000-30049`.
- `RTPENGINE PACKET VERDICT` shows `caller_to_callee=observed callee_to_caller=observed` and `total_rtp_packets` greater than zero.
- `BYE`, `200 OK BYE`, and `RTPENGINE DELETE status=ok` appear at call release.

Small RTPengine `errors=1` counters can appear during NAT learning. Treat them as noise when both packet directions are observed and audio is heard both ways.

## 6. Capture A Wireshark Bundle

Run this from the checked-out PlaySBC source in Cloud Shell, then place and clear both manual calls while the capture is active.

```bash
PYTHONPYCACHEPREFIX=/tmp/playsbc-pycache python3 tools/run_real_device_capture.py \
  --namespace playsbc \
  --duration 120
```

The output is one compact bundle:

```text
logs/Real-Device-Lab/real-device-capture-<timestamp>/
  capture.pcap
  sipmsg.log
  playsbc.log
  rtpengine.log
  rtpengine-verdict.log
  summary.log
```

Open `capture.pcap` in Wireshark. It is timestamp-sorted and merged from PlaySBC and RTPengine capture points, so you do not need separate core/peer PCAPs for manual real-device review.

## 7. Fast Troubleshooting

```bash
kubectl -n playsbc get pods -o wide
kubectl -n playsbc get svc -o wide
kubectl -n playsbc logs deployment/playsbc-playsbc --tail=200
```

Common symptoms:

- No REGISTER: check SIP public IP, UDP 5062, home-router SIP ALG, and OBi provisioning.
- 401 loop: wrong password, token auth still enabled, or realm mismatch.
- OBi address-incomplete: check `INVITE ROUTE SELECTED`; PlaySBC should route using the `To` user when Request-URI is only the AKS public IP.
- Zoiper `Unparsable SDP`: route fallback/echo leaked into a real-device call. Keep `reject_unknown_routes=true` and re-register both endpoints after a pod restart.
- `480 Temporarily Unavailable`: hardphone was not answered before `b2bua_invite_timeout`. Use `60.0`.
- No or one-way audio: check the Azure RTP public LoadBalancer, `rtpengine.advertisedIP`, RTP ports `30000-30049`, and keep `rtpengine_g711_only=true`, `rtpengine_plain_rtp_sdp=true`, `rtpengine_sip_source_address=true`, `rtpengine_media_handover=true`, `rtpengine_nat_wait=true`, and `rtpengine_pierce_nat=true` for the baseline.
- Keepalive noise: OBi/Zoiper may send CRLF or `keep-alive` UDP packets with no CSeq. PlaySBC logs them as `SIP KEEP-ALIVE` and ignores them; they should not create stack traces.

## 8. What v2.4.x Hardens

- Real-device SIP users: `1001` and `1002`.
- Dynamic AKS SIP/RTP public IPs; no hard-coded public IPs.
- Strict real-device routing with no fallback echo for missing registrar routes.
- 60 second outbound answer window for human hardphone pickup.
- G.711-only RTPengine baseline for OBi/Zoiper media before wider codec experiments.
- Plain RTP/AVP SDP normalization for real devices that do not like ICE, RTCP-mux, fingerprint, or WebRTC-style SDP attributes.
- RTPengine SIP-source-address NAT learning so OBi/Zoiper media uses the observed public SIP source instead of private/fragile endpoint SDP.
- RTPengine media-handover learning for real OBi/Zoiper NAT flows where the endpoint media tuple may differ from initial SDP.
- RTPengine `NAT-wait` and `pierce NAT` flags for home-NAT devices that need endpoint pinholes opened before they accept far-end media.
- Locked Azure RTP media range: RTPengine and the public RTP LoadBalancer both use UDP `30000-30049`; Helm fails if they drift.
- Explicit SDP/RTP evidence: inbound offer, outbound offer, callee answer, caller answer, allocated RTPengine ports, learned endpoints, and per-direction packet verdicts.
- OBi-style in-dialog re-INVITE media refreshes get a valid `200 OK` SDP answer instead of `491 Request Pending`.
- Safe UDP NAT keepalive handling for hardphones and softphones.
- Duplicate B2BUA BYE after teardown is answered with `200 OK` when the call ID was just finalized, avoiding noisy harmless `481` responses.
- Manual OBi1022/Zoiper tests can generate one combined SIP/RTP/RTCP `capture.pcap`, `sipmsg.log`, and RTPengine packet verdict evidence bundle.

## 9. Next Roadmap

- Add the real-device capture bundle into the HTML report path instead of keeping it as a manual lab artifact.
- Add real-device RTCP receiver-report, jitter, packet-loss, and MOS-style media-quality evidence.
- Run longer OBi1022 and Zoiper soak calls with re-registration during active calls.
- Validate hardphone/softphone SIP over TCP, SIP over TLS, and SRTP where the endpoint supports it.
- Add multi-device tests: two hardphones plus one softphone, multiple home NAT types, and SIP ALG detection notes.
- Exercise real-device HA: PlaySBC pod restart, RTPengine pod restart, active-active routing, and shared registrar/dialog restore.
- Add Azure production hardening: DNS/FQDN, NSG/firewall templates, dashboard panels for real devices, and cleanup/cost guardrails.
