---
name: improve-python-performance
description: "Profile, benchmark, and optimize Python, NumPy, and JAX/XLA applications. Use when diagnosing performance regressions, latency or throughput problems, memory bloat, CPU/GPU idle time, JIT recompilation churn, or host/device transfer stalls."
---

# Improve Python Performance

Identify and remove performance bottlenecks in Python applications, data
pipelines, and accelerator-backed workloads. Optimize only against measured
evidence from a reproducible workload.

## Principles

1. Measure before modifying. Establish a reproducible baseline and collect a
   profile before proposing an optimization.
2. Choose the target metric explicitly. Distinguish latency, throughput, tail
   latency, memory use, and cold-start cost.
3. Inspect utilization, saturation, and errors across the relevant CPU, memory,
   storage, network, and accelerator resources.
4. Prefer changes to data movement, memory layout, batching, and architecture
   over isolated micro-optimizations.
5. Separate tracing or compilation cost from steady-state execution in
   JIT-compiled systems.

## Workflow

### 1. Define the workload

- Identify the representative input, execution environment, concurrency, and
  success metric.
- Preserve correctness requirements, including numerical tolerances and memory
  limits.

### 2. Establish a baseline

- Automate the benchmark where practical, for example with `pytest-benchmark`
  for functions or `hyperfine` for commands. Avoid ad-hoc `timeit` micro-loops
  that measure an unrepresentative fragment of the workload.
- Control machine-state variance before trusting small differences: CPU
  frequency scaling, thermal throttling, and competing load can outweigh the
  effect being measured.
- Record cold-start and steady-state behavior separately when compilation,
  caching, or initialization is involved.
- Capture enough repetitions to expose variance and relevant latency
  percentiles.

### 3. Profile from broad to narrow

Start with system utilization and low-overhead sampling. Narrow to allocation,
line-level, or accelerator traces only after identifying the relevant resource
or code region. Read [profiler-selection.md](references/profiler-selection.md)
when choosing or operating a profiler.

For JAX, XLA, or accelerator-backed workloads, also read
[accelerated-workloads.md](references/accelerated-workloads.md).

### 4. Classify the bottleneck

Determine whether evidence points to host execution, allocation or memory
pressure, synchronization or data transfer, accelerator execution, or off-CPU
waiting. State the evidence and a testable optimization hypothesis.

Check algorithmic scaling before accepting a resource-level explanation:
measure the workload at two or three input sizes and treat superlinear growth
as evidence of excess work — an O(n²) loop, a linear scan that should be a set
or dict lookup, repeated recomputation of an invariant — rather than of a slow
resource.

### 5. Survey candidate optimizations

Enumerate every candidate the profile supports before choosing one. Aggregate
repeated low-level patterns across call sites — data copies, redundant
serialization, per-item dispatch — because a diffuse pattern can outrank any
single hotspot without appearing hot anywhere. Ask whether the evidence points
to a structural cause such as data flow, batching, or architecture rather than
a local fix.

Present the candidates as a short table — candidate, evidence, bounded impact,
effort, risk — and let the user select the target. Bound each impact estimate
by the profile fraction the candidate touches: eliminating a region that is
40% of runtime caps the speedup at 1.67x.

### 6. Change one variable

Make the smallest change that tests the hypothesis. Keep unrelated cleanup and
speculative optimizations out of the experiment.

### 7. Verify

- Run the relevant behavioral and contract tests.
- Compare outputs using workload-appropriate correctness and numerical checks.
- Rerun the benchmark under the baseline conditions.
- Report the before and after measurements, variance, tradeoffs, and remaining
  uncertainty.
- Keep the change only when it produces a meaningful improvement without an
  unacceptable regression in another required metric.
