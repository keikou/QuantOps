# SRH-01 Lane Boundary / AFG Freeze Connection

## AFG Freeze

```text
AFG-01 through AFG-05 are complete.
No new AFG feature expansion is allowed.
Bugfix, regression, and docs correction only.
```

## SRH Responsibility

```text
- runtime monitoring
- degradation control
- system stability
- safe mode and recovery connection
```

## Boundary With AFG

```text
AFG:
  policy / governance / audit

SRH:
  runtime health / stability / degradation control
```

## Allowed Changes

```text
- runtime health signals
- safe mode control records
- recovery attempts
- degradation state visibility
```

## Forbidden Changes

```text
- policy changes
- RBAC changes
- AFG audit/replay changes
- live strategy changes
```

## Completion Conditions

```text
- degradation control works
- safe mode action is persisted
- recovery attempt is persisted
- AFG frozen surfaces are not mutated
```
