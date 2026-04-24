# ASD-01 Symbolic Alpha Generator

Date: `2026-04-24`
Repo: `QuantOps_github`
Lane: `Alpha Synthesis / Structural Discovery Intelligence`
Packet: `ASD-01`
Status: `active_packet_boundary`

## Task

Make the generator core explicit enough that a future thread can answer:

- which symbolic alpha structures were generated
- what the current structure search state is
- how novelty versus the existing expression library is scored
- which expressions have been accepted into the expression library
- whether symbolic alpha synthesis is effective enough to continue

## Canonical Surfaces

- `GET /system/alpha-synthesis-candidates/latest`
- `GET /system/alpha-structure-search-state/latest`
- `GET /system/alpha-novelty-evaluation/latest`
- `GET /system/alpha-expression-library/latest`
- `GET /system/alpha-synthesis-effectiveness/latest`
