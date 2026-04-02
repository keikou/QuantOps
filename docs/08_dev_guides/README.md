# Development Guides Index

Date: `2026-04-02`
Repo: `QuantOps_github`
Status: `initial_dev_guides_index`

## Purpose

This folder is the canonical entrypoint for implementation and contributor guidance.

It answers:

- which rules should guide code changes
- how to start and verify the local stack
- which regression checks matter before calling work done

## Read First

1. `./current_dev_guide.md`
2. `./verification_guide.md`
3. `../development-rules-v12-vs-quantops.md`
4. `../dev-startup.md`
5. `../ci_regression_packs.md`

## Development Rule

Treat root-level guide docs as source material.
Treat this folder as the canonical entrypoint that tells humans and AI agents which guide to read first.

## Current Focus

- do not reopen completed hardening packets unless a real regression is found
- if implementation continues, it should likely start the next lane beyond hardening/resume
- current default candidate remains `Execution Reality`
