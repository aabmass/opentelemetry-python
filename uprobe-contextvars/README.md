## Running

```console
docker compose up --remove-orphans  --build
```

## Sample output

```console
bpftrace-1  | Trying to attach probe: uretprobe:/usr/lib/libpython3.13.so:context_run*
bpftrace-1  | Attaching to 1 functions
bpftrace-1  | /usr/lib/libpython3.13.so:context_run
bpftrace-1  | Trying to attach probe: uprobe:/usr/lib/libpython3.13.so:context_run*
bpftrace-1  | Attaching to 1 functions
bpftrace-1  | /usr/lib/libpython3.13.so:context_run
bpftrace-1  | Trying to attach probe: uprobe:/usr/lib/libpython3.13.so:PyContext_Exit
bpftrace-1  | Trying to attach probe: uprobe:/usr/lib/libpython3.13.so:PyContext_Enter
bpftrace-1  | Attached 4 probes
bpftrace-1  | tid=3062951 context_run { .self = 0x7fdd35f88900, .args = 0x7fdd36158a98, .nargs = 3, .kwnames = 0x0 }
bpftrace-1  | tid=3062951 return context_run
bpftrace-1  | tid=3062951 context_run { .self = 0x7fdd36188240, .args = 0x7fdd35f37098, .nargs = 2, .kwnames = 0x0 }
bpftrace-1  | tid=3062951 return context_run
bpftrace-1  | tid=3062958 context_run { .self = 0x7fdd35f88900, .args = 0x7fdd3722e938, .nargs = 1, .kwnames = 0x0 }
python-1    | 200
bpftrace-1  | tid=3062958 return context_run
bpftrace-1  | tid=3062951 context_run { .self = 0x7fdd35f8b740, .args = 0x7fdd35ff7758, .nargs = 3, .kwnames = 0x0 }
bpftrace-1  | tid=3062951 return context_run
bpftrace-1  | tid=3062951 context_run { .self = 0x7fdd364f40c0, .args = 0x7fdd3600d588, .nargs = 1, .kwnames = 0x0 }
bpftrace-1  | tid=3062951 return context_run
bpftrace-1  | tid=3062951 context_run { .self = 0x7fdd364320c0, .args = 0x7fdd35f36118, .nargs = 2, .kwnames = 0x0 }
bpftrace-1  | tid=3062951 return context_run
bpftrace-1  | tid=3062951 context_run { .self = 0x7fdd36188240, .args = 0x7fdd35f36118, .nargs = 2, .kwnames = 0x0 }
bpftrace-1  | tid=3062951 return context_run
bpftrace-1  | tid=3062951 context_run { .self = 0x7fdd35f88900, .args = 0x7fdd36158a98, .nargs = 3, .kwnames = 0x0 }
bpftrace-1  | tid=3062951 return context_run
bpftrace-1  | tid=3062951 context_run { .self = 0x7fdd36188240, .args = 0x7fdd35f36118, .nargs = 2, .kwnames = 0x0 }
bpftrace-1  | tid=3062951 return context_run
bpftrace-1  | tid=3062958 context_run { .self = 0x7fdd35f88900, .args = 0x7fdd3722e938, .nargs = 1, .kwnames = 0x0 }
bpftrace-1  | tid=3062958 return context_run
bpftrace-1  | tid=3062951 context_run { .self = 0x7fdd35f8b740, .args = 0x7fdd35ff7758, .nargs = 3, .kwnames = 0x0 }
bpftrace-1  | tid=3062951 return context_run
bpftrace-1  | tid=3062951 context_run { .self = 0x7fdd364f40c0, .args = 0x7fdd3600d738, .nargs = 1, .kwnames = 0x0 }
bpftrace-1  | tid=3062951 return context_run
bpftrace-1  | tid=3062951 context_run { .self = 0x7fdd364320c0, .args = 0x7fdd35fbaf58, .nargs = 2, .kwnames = 0x0 }
bpftrace-1  | tid=3062951 return context_run
bpftrace-1  | tid=3062951 context_run { .self = 0x7fdd36188240, .args = 0x7fdd35fbaf58, .nargs = 2, .kwnames = 0x0 }
python-1    | 200
```

In this example `3062951` is the main event loop thread and `3062958` is a thread pool worker,
given work by `asyncio.to_thread()`. When work is run in the thread pool, asyncio wraps that in
`context_run()` so you can track which thread started the work. The [self
argument](https://github.com/python/cpython/blob/v3.13.9/Python/context.c#L649) is a pointer to
the [Context object](https://docs.python.org/3/library/contextvars.html#contextvars.Context). One thing to note is that python may re-use context objects in memory.

In the above example, Context `0x7fdd35f88900` moves between the two threads.
```console
bpftrace-1  | tid=3062951 context_run { .self = 0x7fdd35f88900, .args = 0x7fdd36158a98, .nargs = 3, .kwnames = 0x0 }
...
bpftrace-1  | tid=3062958 context_run { .self = 0x7fdd35f88900, .args = 0x7fdd3722e938, .nargs = 1, .kwnames = 0x0 }
...
bpftrace-1  | tid=3062951 context_run { .self = 0x7fdd35f88900, .args = 0x7fdd36158a98, .nargs = 3, .kwnames = 0x0 }
...
bpftrace-1  | tid=3062958 context_run { .self = 0x7fdd35f88900, .args = 0x7fdd3722e938, .nargs = 1, .kwnames = 0x0 }
```
