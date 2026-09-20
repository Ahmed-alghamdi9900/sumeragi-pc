# Architecture decision: deferred pending source evidence

No runtime or renderer backend has been selected. A CPU instruction-set match
alone cannot establish Windows compatibility.

| Candidate | Evidence needed before selection |
|---|---|
| Static recompilation | Accessible code, control-flow coverage, relocation and indirect-call handling |
| Binary translation | ABI/platform boundaries, timing accuracy, maintenance and runtime costs |
| Source reimplementation | Recoverable behavior, subsystem scope, reference validation cost |
| API compatibility | Import surface, kernel/graphics assumptions, platform isolation feasibility |
| Hybrid | Measured boundaries and small working proofs for each combined technique |

First identify the build and accessible executable representation. Then map
dependencies and test a small isolated function/platform boundary. Compare
accuracy, performance, maintainability, modding, portability, debugging difficulty,
and engineering cost. Renderer selection needs shader and API evidence. Preserve
original rendering before exposing tested enhancements; no placebo settings.
