# Rsprof

The event-based and debugger-based program tracer for Rust.

---

## Introduction

**Rsprof** is a tool to create tracer for Rust programming language. It utilize `lldb` as its bases and provides basic utilities to perform event based tracing and result visualization powered by Drcctprof viewer.

Currently, a memory tracer is provided as an example.

## Build and Installation

### Rsprof

Install Python packages:

```
protobuf==3.6.1
rust-demangler==1.0
```

Then clone this repo:

```bash
git clone https://github.com/yhl1219/rsprof.git
```

After you _clone_ this repo, you need your lldb to import related comands. This could be done by:

```lldb
command script import {path to rsprof}
```

For example, if you place your repo at `~`, then it would be:

```lldb
command script import ~/rsprof/rsprof
```

This line could be added to `~/.lldbinit` so that it would be imported everytime automatically. Read more about the initialization file of `lldb` here: https://lldb.llvm.org/man/lldb.html at section **CONFIGURATION FILE**

### Rsprof-Stub

To use some functionality with the tracer, you need to build your rust program with some additional library and they are provided by `rsprof-stub` crate.

To use `memtrace` function, you would use a memory allocator wrapper. This is done by adding:

```rust
#[global_allocator]
static RSPROF_ALLOCATOR: RsprofAllocator<System> = RsprofAllocator {
    allocator: System {}
}
```

in your `main.rs`

Note that allocator `System` could be changed to your allocator. 

## Usage

General usage is using the following command format:

```
rsprof {action}
```

action could be the following: `enable`, `disable`, `list`, `report`.

**enable**, **disable**: enable/disable the listed modules, for example, if you want to enable module `memtrace`, then you need:

```
rsprof -m memtrace enable
```

to enable multiple modules, you could do this by using comma in between modules:

```
rsprof -m memtrace,clone enable
```

After enabling some modules, using the lldb command `r`(`run`'s abbr) to execute your program and modules would collect their events and data.

**list**: list enabled modules

**report**: let enabled modules report tracing result, for example, if you want `memtrace` to report its result into a file `out`, then:

```
rsprof -m memtrace -o out report
```

and a file names `out.memtrace.prof` would be generated. You could view it using vscode plugin [DrCCTProf Viewer](https://marketplace.visualstudio.com/items?itemName=Xuhpclab.drcctprof-vscode-extension)

## Design 

By utilizing the custom script function provided by `lldb`, rsprof could set breakpoints and breakpoint callbacks automatically by tracing modules. Each tracing module would define its own functionality and breakpoints with a set of callbacks.

At each breakpoint, the callback function of the tracing module would be called, thus, an _event_ of the tracing module is invoked. The module would perform stacktrace, explore function arguments and other things to record a full tracing event.

Events would then be serialized into `drcctprof` format for visualization. Each module could define its own serialization scheme, or report other output format like graphs or charts.

For more information, see documentation.