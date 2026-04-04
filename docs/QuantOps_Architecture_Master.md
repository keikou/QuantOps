# QuantOps Architecture Master

**Project:** QuantOps V12  
**Document type:** Control Plane Architecture  
**Status:** Canonical Draft (Post-Phase7 Hardening)

---

## 1. Overview

QuantOps is the **control plane** of the V12 system.

It provides:
- operator-facing dashboards
- orchestration and control
- monitoring and alerting
- aggregation of V12 truth into usable views

QuantOps does NOT own trading truth.  
It consumes, normalizes, and presents it.

---

## 2. System Architecture

### 2.1 Layers

Frontend (Next.js)  
↓  
QuantOps API (FastAPI)  
↓  
QuantOps Worker  
↓  
V12 API  

---

## 3. Core Modules

### 3.1 Dashboard
- Overview
- Execution
- Portfolio
- Risk
- Monitoring

### 3.2 Scheduler
- cron-based runs
- manual triggers

### 3.3 Control
- run trigger
- strategy control
- system mode switching

### 3.4 Monitoring
- health checks
- logs
- alerts

### 3.5 Analytics (View Layer)
- PnL summaries
- execution quality
- alpha metrics

### 3.6 Risk View
- exposure
- drawdown
- limits

### 3.7 Config / Registry
- strategy configs
- environment configs

### 3.8 Admin
- system control
- maintenance operations

---

## 4. Truth Runtime Design

### Execution Truth
source: execution_fills (V12)

### Market Truth
source: market_prices_latest (V12)

### Position Layer
source: position_snapshots_latest (derived from V12)

### Equity Layer
source: equity_snapshots, cash_ledger (V12)

---

## 5. UI Binding Rules

Execution → execution_fills  
Portfolio → position_snapshots_latest  
Overview → equity_snapshots  

---

## 6. Worker Architecture

- scheduler loop
- analytics refresh
- risk snapshot generation

---

## 7. API Responsibilities

QuantOps API:
- aggregates V12 data
- normalizes for frontend
- exposes control endpoints

It must NOT:
- redefine trading truth
- synthesize execution data

---

## 8. Data Flow

V12 → QuantOps ingestion → normalization → frontend rendering

---

## 9. Failure Handling

States:
- healthy
- degraded
- stale
- unavailable

QuantOps must surface these explicitly.

---

## 10. Design Principles

- DB = truth source (via V12)
- UI = projection only
- QuantOps = observer + controller
- No silent fallback
