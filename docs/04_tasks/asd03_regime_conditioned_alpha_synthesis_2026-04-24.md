# ASD-03 Regime-Conditioned Alpha Synthesis

Date: `2026-04-24`
Repo: `QuantOps_github`
Lane: `Alpha Synthesis / Structural Discovery Intelligence`
Packet: `ASD-03`
Status: `active_packet_boundary`

## Task

Make the symbolic alpha generator core explicit enough that a future thread can answer:

- which regime-conditioned synthesis agenda is active
- which candidates are being targeted to the current regime
- how regime fit is evaluated
- how expressions map to regime and family targets
- whether regime-conditioned synthesis is effective enough to continue

## Canonical Surfaces

- `GET /system/alpha-regime-synthesis-agenda/latest`
- `GET /system/alpha-regime-targeted-candidates/latest`
- `GET /system/alpha-regime-fit-evaluation/latest`
- `GET /system/alpha-regime-expression-map/latest`
- `GET /system/alpha-regime-synthesis-effectiveness/latest`
