# SRH-01 Degradation Detection & Control Workflow

## Flow

```text
1. signal ingest
2. health computation
3. degradation detection
4. severity classification
5. control decision
6. safe mode / recovery
```

## Detection

```text
- threshold breach
- component score deterioration
- composite system score deterioration
```

## Control Actions

```text
S1:
  log only

S2:
  partial throttle

S3:
  safe mode

S4:
  halt
```

## Recovery

```text
- observe only
- retry and throttle
- safe mode then recover
- operator escalation
```

## Escalation

```text
S3 and above require operator-visible control and recovery records.
```

