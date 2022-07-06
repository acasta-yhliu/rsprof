# Rsprof

The not so profiler for rust, only within your lldb

---

## Introduction

**Rsprof** is a tool created for light weight profiling for Rust programming language. It is not a full profiler like `perf`, where you could see things like stacktrace, flamegraph or something like that, but a tool for function tracing and special profiling aspects like memory allocation, uncessary clone and other things.

Since it is only built against lldb, it's easy for someone to install and use it. Only you need is import the `rsprof` module inside lldb and start with the `rsprof` command.

## Build

```bash
pip3 install rsprof
```

Everything should be done by pip3, including adding import script in your `.lldbinit` file.