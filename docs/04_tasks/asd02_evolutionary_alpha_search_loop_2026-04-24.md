# ASD-02 Evolutionary Alpha Search Loop

Date: `2026-04-24`
Repo: `QuantOps_github`
Lane: `Alpha Synthesis / Structural Discovery Intelligence`
Packet: `ASD-02`
Status: `active_packet_boundary`

## Task

Make the symbolic alpha search loop explicit enough that a future thread can answer:

- which expressions are eligible parents
- which mutation candidates were generated
- which crossover candidates were generated
- what the current evolutionary search state is
- whether the evolutionary search loop is effective enough to continue

## Canonical Surfaces

- `GET /system/alpha-parent-candidates/latest`
- `GET /system/alpha-mutation-candidates/latest`
- `GET /system/alpha-crossover-candidates/latest`
- `GET /system/alpha-evolution-search-state/latest`
- `GET /system/alpha-evolution-effectiveness/latest`
