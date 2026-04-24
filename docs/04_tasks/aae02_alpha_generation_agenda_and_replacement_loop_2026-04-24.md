# AAE-02 Alpha Generation Agenda And Replacement Loop

Date: `2026-04-24`
Repo: `QuantOps_github`
Lane: `Autonomous Alpha Expansion / Strategy Generation Intelligence`
Packet: `AAE-02`
Status: `active_packet_boundary`

## Task

Make the next-step alpha expansion loop explicit enough that a future thread can answer:

- what should be generated next
- which experiments are ready
- which candidates should replace fragile inventory
- whether replacement is actually happening

## Required Output

Produce:

- one packet plan doc
- one verifier script
- explicit `/system/*` surfaces for generation agenda, experiment docket, replacement decision, replacement state, and expansion effectiveness

## Canonical Surfaces

- `GET /system/alpha-generation-agenda/latest`
- `GET /system/alpha-experiment-docket/latest`
- `GET /system/alpha-replacement-decision/latest`
- `GET /system/alpha-replacement-state/latest`
- `GET /system/alpha-expansion-effectiveness/latest`
