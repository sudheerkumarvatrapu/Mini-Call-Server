# PlaySBC v2.2.1

AKS regression hotfix release.

## Why

The v2.2.0 AKS regression run exposed two release-line issues:

- PlaySBC server headers still reported `2.1.1` even when the chart/version metadata was `2.2.0`.
- The real-device NAT routing fix was too broad for Kubernetes SIPp pods. It used the REGISTER packet source port for private Contact addresses even when Contact host and packet source host were the same pod IP. In AKS SIPp regression this sent B2BUA INVITEs to the REGISTER port `5070` instead of the SIPp UAS port `5060`, causing `480 Temporarily Unavailable`.

## What Changed

- Align `PLAYSBC_VERSION` with the release version.
- Keep real-device NAT routing when Contact host differs from packet source host.
- Preserve SIP Contact-port routing when Contact host matches packet source host, which restores Kubernetes SIPp REGISTER + B2BUA call profiles.
- Add a focused unit test covering the AKS SIPp pod case.

## Validation

- Focused registrar routing tests passed.
- SIP keepalive handling test passed.

## Notes

This hotfix is scoped to AKS regression correctness and release version reporting. It does not change the OBi1022/Zoiper RTP media hardening track.
