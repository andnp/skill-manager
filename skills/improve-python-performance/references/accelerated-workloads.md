# Accelerated Workloads

Use this guidance for JAX, XLA, and GPU- or TPU-backed workloads after
establishing a representative baseline.

## Separate compilation from execution

Measure cold compilation explicitly and exclude it from steady-state timing.
JAX dispatch is asynchronous on accelerators, so block on the result before
stopping an execution timer:

```python
t0 = time.perf_counter()
result = jitted_step(params, inputs).block_until_ready()
elapsed = time.perf_counter() - t0
```

Track input shapes, dtypes, and static arguments when investigating unexpected
JAX recompilation. Stable shapes or a small set of padded buckets can reduce
compilation churn when the workload permits it.

## Find synchronization and transfer stalls

Python value access can synchronize execution and transfer device data to the
host. Inspect logging, conditionals, callbacks, `float(array)`, `array.item()`,
and NumPy conversion in hot paths. Prefer compiled control flow when the
condition belongs in the accelerated computation.

Use accelerator traces to determine whether the workload is limited by host
dispatch, transfers, memory bandwidth, compute, or input starvation before
changing graph structure or batch sizes.

## Test graph-level changes

Treat `jax.lax.scan`, rematerialization, fusion, padding, and layout changes as
hypotheses with tradeoffs:

- `jax.lax.scan` can reduce Python dispatch and compilation graph size for
  repeated computation.
- `jax.checkpoint` can reduce stored activations at the cost of recomputation.
- Padding and larger batches can improve device utilization while increasing
  memory use or request latency.
- Contiguous layouts and hardware-friendly dimensions can help some kernels but
  may add copies or waste computation.

Measure compilation time, steady-state time, peak memory, and required latency
or throughput metrics before keeping any such change.
