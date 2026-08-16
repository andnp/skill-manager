# Profiler Selection

Start wide and non-intrusive, then narrow to the resource or code region that
the evidence identifies.

| Tool | Type | Typical use | Important blind spots |
|---|---|---|---|
| `py-spy` | Statistical sampling | CPU flame graphs and thread snapshots with low overhead | Can miss rare or short events and does not trace allocations |
| `scalene` | CPU, allocation, and GPU sampling | Separating Python, native, and allocation time | Adds more overhead than a CPU-only sampler; GPU metrics are approximate |
| `memray` | Allocation tracing | Heap growth, allocation hotspots, and leak investigation | Produces large traces and does not measure CPU time |
| `cProfile` | Deterministic call instrumentation | Call counts and cumulative Python execution time | Call overhead can distort small, frequently called functions |
| `line_profiler` | Line instrumentation | Statements inside an already identified hotspot | High overhead and narrow scope |
| `jax.profiler` | Accelerator tracing | Host/device transfers, compiled operations, and stream activity | Traces can be large and require a compatible viewer |
| `nvidia-smi` / Nsight Systems | GPU utilization and system tracing | Confirming accelerator idleness, kernel gaps, and transfer activity | Little Python-level attribution without added annotation |

## Profiling sequence

1. Inspect utilization, saturation, errors, and elapsed time at the system level.
2. Capture a representative sampling profile.
3. Investigate allocations when memory growth, allocator activity, or garbage
   collection is implicated.
4. Instrument individual functions or lines only after sampling identifies a
   hotspot.
5. Use accelerator traces when host sampling shows dispatch, synchronization,
   or device-wait behavior.

Use non-round sampling frequencies such as 99 Hz or 199 Hz when periodic work
could synchronize with the sampler. Inspect blocked stacks or system scheduler
traces when the workload is waiting on I/O, locks, subprocesses, or accelerator
completion. Use `py-spy dump` to snapshot the thread stacks of a hung or
deadlocked process.

Always confirm profiler findings with unprofiled end-to-end measurements.

## Example commands

```bash
py-spy record -o profile.svg --rate 199 --pid <PID>
py-spy record -o profile.svg -- python main.py
py-spy dump --pid <PID>

scalene main.py

memray run -o mem_trace.bin main.py
memray flamegraph mem_trace.bin
memray flamegraph --leaks mem_trace.bin
```
