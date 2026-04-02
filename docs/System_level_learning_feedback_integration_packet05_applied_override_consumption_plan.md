# System-Level Learning / Feedback Integration Packet 05

Date: `2026-04-02`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Lane: `System-Level Learning / Feedback Integration`
Packet: `05`
Status: `defined`

## Goal

Show that resolved overrides are consumed by the next cycle.

## Invariant

`/system/learning-applied-consumption/latest` must transform `Packet 04` resolved overrides into explicit next-cycle consumption surfaces.

## Acceptance

The packet is acceptable when:

- the surface returns `run_id`, `cycle_id`, `mode`, `consumed_run_id`, and `consumed_cycle_id`
- each family item includes `selection_consumption`, `capital_consumption`, `review_consumption`, and `runtime_consumption`
- each family item exposes `consumed_effect`
- the surface returns `applied_consumption_summary.system_consumption_action`
- a verifier can confirm representative consumed states and summary

## Route

- `GET /system/learning-applied-consumption/latest`
