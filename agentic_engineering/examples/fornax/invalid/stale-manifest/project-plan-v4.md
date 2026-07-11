---
plan_id: PLAN-FORNAX-V4
plan_version: 4
status: authoritative
---

# Fornax Example Plan v4

## Outcome

Prove that a bounded distributed inference engine can execute one model across
heterogeneous commodity nodes while preserving numerical correctness,
backpressure, cancellation, and traceable evidence.

The accountable human owns scope and every gate decision. Agents may implement,
inspect, and validate bounded work, but may not promote a simulation result into a
physical capability claim.

## Scope

In scope:

- a versioned stage protocol and runtime backend;
- distributed scheduling and transport;
- a reference numerical path;
- physical backend and multinode validation; and
- diagnosable operator workflows at productization.

Out of scope:

- a graphical frontend;
- training or fine-tuning; and
- an unattended production deployment.

## Domain Functions

| Code | Function | Current need |
|---|---|---|
| RT | Runtime/backend integration | Active |
| DIST | Distributed scheduler | Active |
| LLM | Numerical correctness | Active; validates RT output |
| NET | Networking and security | Active for physical testing |
| SRE | Observability and evidence custody | Active |
| OX | Operator experience | Active for the operator CLI; fresh-operator validation at G5 |
| FE | Graphical frontend delivery | Omitted; no graphical surface is planned |

## Evidence Classes

| Class | Meaning | Claim authority |
|---|---|---|
| T0 | Contract/unit/property evidence | Contract behavior only |
| T1 | Simulation or loopback evidence | Simulated behavior only |
| T2 | One physical backend | Backend-specific behavior |
| T3 | Multiple physical nodes and a real network | G2 distributed-correctness claims |
| T5 | Fresh operator exercise | Productization and operability claims |

## Gates

| Gate | Decision | Required evidence |
|---|---|---|
| G1 | Authorize bounded implementation | T0/T1 contract and simulation evidence |
| G2 | Accept physical distributed correctness | T2 parity plus T3 generation, transport, cancellation, and backpressure evidence |
| G5 | Accept productization | T5 install, diagnose, upgrade, and rollback evidence |

Every gate outcome is `COMMIT`, `NARROW`, `KILL`, or `PARK`. The example
instance is at G2; only the exact claims accepted in `evidence/EV-G2-001.yaml` may
advance.
