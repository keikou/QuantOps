# Task: Contract Doc Update

Date: `2026-04-05`
Status: `reusable`

## Goal

Add or refine an interface contract doc so operators and AI do not need to recover meaning from code first.

## Why Now

The interface layer is one of the highest-leverage docs layers in the current repo state.

## Inputs

- `../07_interfaces/README.md`
- `../07_interfaces/current_contracts.md`
- target endpoint or payload surface
- the closest existing interface doc

## Steps

1. identify the missing contract boundary
2. write the smallest doc that makes the contract explicit
3. connect the new doc from `README.md` and `current_contracts.md`
4. run the interface docs verifier

## Outputs

- one new or updated interface contract doc
- updated routing from interface entrypoints

## Non-Goals

- rewriting every schema exhaustively
- changing endpoint behavior
- mixing task execution details into interface docs

## Completion Check

- the interface meaning is readable without code-first recovery
- `verify_interfaces_docs.py` still passes
