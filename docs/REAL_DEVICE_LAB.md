# PlaySBC Real Device Lab

Use this runbook for the first AKS test with one hardphone and one softphone.

```text
OBi1022 1001 -> Internet/NAT -> Azure LB UDP 5062 -> PlaySBC -> RTPengine -> Zoiper 1002
```

## 1. Upgrade AKS For Real Devices

Run in Azure Cloud Shell after the `v2.0.0` release/images are published.

```bash
export PLAYSBC_VERSION=2.0.0
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
  --set-string playsbc.config.sip_advertised_ip="$SIP_PUBLIC_IP" \
  --set-string playsbc.config.b2bua_advertised_ip="$SIP_PUBLIC_IP" \
  --set authSecret.enabled=true \
  --set-string authSecret.users.1001=secret-password \
  --set-string authSecret.users.1002=secret-password

kubectl -n playsbc rollout restart deployment/playsbc-playsbc deployment/playsbc-playsbc-rtpengine
kubectl -n playsbc rollout status deployment/playsbc-playsbc --timeout=180s
kubectl -n playsbc rollout status deployment/playsbc-playsbc-rtpengine --timeout=180s
```

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

## 4. Monitor Registration And Calls

```bash
kubectl -n playsbc logs deployment/playsbc-playsbc -f --since=10m \
  | grep -aE "PlaySBC version|REGISTER|Registered|SIP INVITE|SIP ACK|SIP BYE|SIP TX response|INVITE ROUTE|RTPENGINE|CODEC CLAMP|KEEP-ALIVE|1001|1002"
```

Expected registration:

```text
Challenged REGISTER for 1001
Registered 1001 -> sip:1001@...
Challenged REGISTER for 1002
Registered 1002 -> sip:1002@...
```

Expected call tests:

```text
OBi1022 1001 -> Zoiper 1002
Zoiper 1002 -> OBi1022 1001
```

The OBi can register with a private Contact such as `192.168.1.9:5060`. PlaySBC keeps that Contact in SIP, but sends packets to the observed public REGISTER source so AKS can reach the device through NAT.

## 5. Fast Troubleshooting

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
- No or one-way audio: check the Azure RTP public LoadBalancer, `rtpengine.advertisedIP`, and keep `rtpengine_g711_only=true` plus `rtpengine_plain_rtp_sdp=true` for the baseline.
- Keepalive noise: OBi/Zoiper may send CRLF or `keep-alive` UDP packets with no CSeq. PlaySBC logs them as `SIP KEEP-ALIVE` and ignores them; they should not create stack traces.

## 6. What v2.0.0 Hardens

- Real-device SIP users: `1001` and `1002`.
- Dynamic AKS SIP/RTP public IPs; no hard-coded public IPs.
- Strict real-device routing with no fallback echo for missing registrar routes.
- 60 second outbound answer window for human hardphone pickup.
- G.711-only RTPengine baseline for OBi/Zoiper media before wider codec experiments.
- Plain RTP/AVP SDP normalization for real devices that do not like ICE, RTCP-mux, fingerprint, or WebRTC-style SDP attributes.
- Safe UDP NAT keepalive handling for hardphones and softphones.
