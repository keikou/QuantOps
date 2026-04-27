# SRH-03 Operator Notification Lifecycle Design

## Purpose

Operator notifications convert escalation decisions into operator-visible work items with lifecycle and acknowledgement tracking.

## Lifecycle

- `CREATED`
- `DELIVERED`
- `ACK_REQUIRED`
- `ACKED`
- `ESCALATED`
- `RESOLVED`
- `EXPIRED`

## Channels

- `OPERATOR_QUEUE`
- `SYSTEM_LOG`
- `PAGER`
- `EMAIL`
- `WEBHOOK`

## Acknowledgement

CRITICAL and EMERGENCY notifications require acknowledgement. ACK records are stored append-only and update the notification status to `ACKED`.

## Invariants

- notification references `escalation_id`
- ACK references `notification_id`
- ACK does not mutate the source SRH event
- duplicate ACK is idempotent from the operator point of view
