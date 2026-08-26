# PlaySBC v2.5.3

PlaySBC v2.5.3 is a focused TLS startup hotfix for the isolated kind real-device lab.

## Local Real-Device Lab

- Do not require `/etc/playsbc-tls/ca.crt` when TLS peer verification is disabled.
- Keep `tls.crt` and `tls.key` mandatory whenever TLS is enabled.
- Continue to default `tls_cafile` to the mounted Secret CA only when `tls_verify_peer=true` and no explicit CA path is configured.
- Document the standard Kubernetes TLS Secret contract used by the OBi1022 and Zoiper lab.

## Evidence Hardening

- Keep the v2.5.2 combined PCAP, SIP ladder, RTP/RTCP verdict, and archive contracts unchanged while making the TLS startup prerequisite explicit.

## Compatibility

- No SIP routing, RTPengine, RTP/RTCP, AKS exposure, HA, regression-profile, or AI Voice Gateway behavior changed.
- Existing AKS real-device, AKS regression, active-active kind, local SIPp, Docker, and AI/Rasa configuration contracts remain unchanged.

## Validation

- The complete 320-test repository suite passes.
- The local real-device Helm profile renders with TLS enabled and an empty CA path when peer verification is disabled.
- A live `kind-playsbc-real-device` deployment passed all preflight checks with PlaySBC and RTPengine ready, all 53 host-port mappings present, and SIP/RTP advertised as the Mac LAN address.
