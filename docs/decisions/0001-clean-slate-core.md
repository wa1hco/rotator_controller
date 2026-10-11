# ADR 0001: Clean-slate firmware core

- Status: Accepted
- Date: 2026-10-11

## Context

The WA1HCO fork of K3NG's rotator controller is a working Arduino sketch
with a large set of compile-time features. It is hard to unit-test, and
changing rotator type or protocol means a rebuild. The system overview
rejects that monolith.

## Decision

The firmware in this repository is a new C++17 core with explicit
interfaces (HAL, position sensor, axis drive, per-axis motion state
machine, protocol modules, versioned settings). It is not a refactor of
the K3NG sketch. K3NG remains the reference for behavior and for the
simulator that was copied in.

The core does not use Arduino types. A host build links the same core
against fakes. The board target is an STM32F407VGT6 (ADR 0014). That
choice stays out of the core.

## Consequences

`software/firmware/` starts as a skeleton. GS-232 is the first protocol;
hamlib rotctld comes later. The copied simulator still speaks to a K3NG
process until a host build of this core replaces that process.
