# PlaySBC Real Device Lab

Use this page when registering a home SIP phone or softphone to PlaySBC running in AKS.

## Target Lab

```text
OBi1022 / hardphone 1001
        -> Internet / NAT
        -> Azure LoadBalancer UDP 5062
        -> PlaySBC
        -> RTPengine
        -> Zoiper / softphone 1002
```

## 1. Get The PlaySBC SIP IP

```bash
kubectl -n playsbc get svc playsbc-playsbc-azure-sip-public \
  -o jsonpath='{.status.loadBalancer.ingress[0].ip}{"\n"}'
```

Use the returned IP as the SIP registrar/proxy.

## 2. Enable Lab SIP Users

For the first real-device test, keep credentials simple and private to the lab.

```bash
helm upgrade --install playsbc \
  https://github.com/sudheerkumarvatrapu/PlaySBC/releases/download/v1.6.1/playsbc-1.6.1.tgz \
  --namespace playsbc \
  --reuse-values \
  --set authSecret.enabled=true \
  --set-string authSecret.users.1001=secret-password \
  --set-string authSecret.users.1002=secret-password
```

## 3. Configure OBi1022 As `1001`

Open the phone UI:

```text
http://192.168.1.9
```

First disable provider auto-provisioning if it is still active:

```text
System Management -> Auto Provisioning
OBiTALK Provisioning: Disabled
ITSP Provisioning: Disabled
Firmware Update: Manual or Disabled
Submit, then reboot if requested.
```

Then configure SP1:

```text
Service Providers -> ITSP Profile A -> SIP
ProxyServer: <PlaySBC public SIP IP>
ProxyServerPort: 5062
ProxyServerTransport: UDP
RegistrarServer: <PlaySBC public SIP IP>
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
```

## 4. Configure Zoiper As `1002`

```text
Username: 1002
Password: secret-password
Domain / Host: <PlaySBC public SIP IP>:5062
Transport: UDP
Outbound proxy: blank
```

## 5. Verify Registration

Watch PlaySBC logs:

```bash
kubectl -n playsbc logs deployment/playsbc-playsbc -f | grep -E "REGISTER|Registered|401|403"
```

Expected for digest auth:

```text
Challenged REGISTER for 1001
Registered 1001 -> sip:1001@...
Challenged REGISTER for 1002
Registered 1002 -> sip:1002@...
```

## 6. First Calls

Try these in order:

```text
OBi1022 1001 -> Zoiper 1002
Zoiper 1002 -> OBi1022 1001
```

If the OBi Contact contains a private address such as `192.168.1.9`, PlaySBC keeps the SIP Contact as the Request-URI but sends packets to the observed REGISTER source address. That makes home-NAT hardphone testing usable in the AKS lab.

## 7. Troubleshooting

```bash
kubectl -n playsbc logs deployment/playsbc-playsbc --tail=200
kubectl -n playsbc get svc -o wide
kubectl -n playsbc get pods -o wide
```

Common issues:

- No REGISTER: check phone SIP server IP, UDP 5062 reachability, and home router SIP ALG.
- 401 repeats forever: wrong SIP password or realm mismatch.
- REGISTER passes but inbound call fails: confirm the log shows the packet destination is the observed source, not only the private Contact.
- One-way audio: check RTPengine public media service exposure and home NAT/firewall behavior.

## 8. Hurdles From The First OBi1022 AKS Test

What we saw:

```text
REGISTER from <home-public-ip>:5060
Challenged REGISTER for 1001
REGISTER from <home-public-ip>:5060
Registered 1001 -> sip:1001@192.168.1.9:5060 expires=300
```

The important lessons:

- If OBi status says `Retrying Register (server=0.0.0.0:0)`, Profile A SIP values are not being applied yet.
- On OBi pages, clear the field `Default` checkbox before changing a value.
- For direct AKS public IP testing, `X_DnsSrv` must be disabled.
- For PlaySBC digest auth, `X_UseTokenAuth` must be disabled.
- OBi backups may not show the password, so retype `AuthPassword` manually after restoring or editing config.
- A private Contact such as `192.168.1.9:5060` is normal behind home NAT. PlaySBC v1.6.1 routes the outbound packet to the observed REGISTER source while preserving the SIP Contact as the Request-URI.
