from rsprof.tracing import TracingEvent, TracingModule
from lldb import (
    SBFrame,
    SBBreakpointLocation,
)
from rsprof.traceutil import stacktrace_from_sbframe, StackTrace
from rsprof.lldbutil import get_function_parameter


MODULE = TracingModule("memory")


class MemoryEvent(TracingEvent):
    def __init__(self, stacktrace: StackTrace) -> None:
        super().__init__(stacktrace)


@MODULE.event
class AllocEvent(MemoryEvent):
    def __init__(
        self, stacktrace: StackTrace, size: int, align: int
    ) -> None:
        super().__init__(stacktrace)
        self.size = size
        self.align = align

    def serialize(self):
        return self.base_serialize({"size": self.size, "align": self.align})


@MODULE.event
class ReallocEvent(MemoryEvent):
    def __init__(self, stacktrace: StackTrace, old_addr: int, old_size: int, align: int, new_size: int) -> None:
        super().__init__(stacktrace)
        self.old_addr = old_addr
        self.size = old_size
        self.align = align
        self.new_addr = new_size

    def serialize(self):
        return self.base_serialize({"old_addr": self.old_addr, "size": self.size, "align": self.align, "new_addr": self.new_addr})


@MODULE.callback_name("__rust_alloc")
def rust_alloc(frame: SBFrame, loc: SBBreakpointLocation, extra_args, interal_dict):
    stacktrace = stacktrace_from_sbframe(frame)

    size, align = get_function_parameter(frame, ("u", "u"))

    MODULE.events.append(AllocEvent(
        stacktrace, size, align))


@MODULE.callback_name("__rust_alloc_zeroed")
def rust_alloc_zeroed(frame: SBFrame, loc: SBBreakpointLocation, extra_args, interal_dict):
    stacktrace = stacktrace_from_sbframe(frame)

    size, align = get_function_parameter(frame, ("u", "u"))

    MODULE.events.append(AllocEvent(stacktrace, size, align))


@MODULE.callback_name("__rust_realloc")
def rust_realloc(frame: SBFrame, loc: SBBreakpointLocation, extra_args, interal_dict):
    stacktrace = stacktrace_from_sbframe(frame)

    old_addr, old_size, align, new_size = get_function_parameter(
        frame, ("u", "u", "u", "u"))

    MODULE.events.append(ReallocEvent(
        stacktrace, old_addr, old_size, align, new_size))

# currently, there's no need to perform deallocation tracing since we are not tracing
# the entire heap, which, until we get the return value of __rust_alloc

# @MODULE.callback_name("__rust_dealloc", "in")
# def rust_dealloc(frame: SBFrame, loc: SBBreakpointLocation, extra_args, interal_dict):
#     pass


@MODULE.callback_report
def report(prog_module: str):
    return MODULE.serialize(filter_module=prog_module)
