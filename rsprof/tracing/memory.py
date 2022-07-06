from rsprof.tracing import TracingModule

MODULE = TracingModule("memory")


@MODULE.callback_name("__rust_alloc", "in")
def memory_breakpoint_callback(a, b, c, d):
    print("breakpoint main hit", a)
