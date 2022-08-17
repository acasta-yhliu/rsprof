from typing import Optional
from rsprof.proto import Event, ProfileBuilder
from rsprof.tracing import TracingEvent, TracingModule
from lldb import (
    SBFrame,
    SBBreakpointLocation,
)
from rsprof.traceutil import (
    stacktrace_from_sbframe,
    StackTrace,
)
from rsprof.lldbutil import get_function_parameter


MODULE = TracingModule("memory")


class MemoryEvent(TracingEvent):
    def __init__(self, stacktrace: StackTrace) -> None:
        super().__init__(stacktrace)


@MODULE.event
class AllocEvent(MemoryEvent):
    def __init__(self, stacktrace: StackTrace, size: int, align: int) -> None:
        super().__init__(stacktrace)
        self.size = size
        self.align = align


@MODULE.event
class ReallocEvent(MemoryEvent):
    def __init__(
        self,
        stacktrace: StackTrace,
        old_addr: int,
        old_size: int,
        align: int,
        new_size: int,
    ) -> None:
        super().__init__(stacktrace)
        self.old_addr = old_addr
        self.old_size = old_size
        self.size = new_size
        self.align = align


@MODULE.event
class DeallocEvent(MemoryEvent):
    def __init__(
        self, stacktrace: StackTrace, addr: int, size: int, align: int
    ) -> None:
        super().__init__(stacktrace)
        self.addr = addr
        self.size = size
        self.align = align


@MODULE.callback_name("__rust_alloc")
def rust_alloc(frame: SBFrame, loc: SBBreakpointLocation, extra_args, interal_dict):
    stacktrace = stacktrace_from_sbframe(frame)

    size, align = get_function_parameter(frame, ("u", "u"))

    MODULE.events.append(AllocEvent(stacktrace, size, align))


@MODULE.callback_name("__rust_alloc_zeroed")
def rust_alloc_zeroed(
    frame: SBFrame, loc: SBBreakpointLocation, extra_args, interal_dict
):
    stacktrace = stacktrace_from_sbframe(frame)

    size, align = get_function_parameter(frame, ("u", "u"))

    MODULE.events.append(AllocEvent(stacktrace, size, align))


@MODULE.callback_name("__rust_realloc")
def rust_realloc(frame: SBFrame, loc: SBBreakpointLocation, extra_args, interal_dict):
    stacktrace = stacktrace_from_sbframe(frame)

    old_addr, old_size, align, new_size = get_function_parameter(
        frame, ("u", "u", "u", "u")
    )

    MODULE.events.append(ReallocEvent(stacktrace, old_addr, old_size, align, new_size))


@MODULE.callback_name("__rust_dealloc")
def rust_dealloc(frame: SBFrame, loc: SBBreakpointLocation, extra_args, interal_dict):
    stacktrace = stacktrace_from_sbframe(frame)

    addr, size, align = get_function_parameter(frame, ("u", "u", "u"))

    MODULE.append_event(DeallocEvent(stacktrace, addr, size, align))


@MODULE.callback_report
def report(output_postfix: Optional[str]):
    profile_builder = ProfileBuilder(
        ("bytes", "allocation size"), ("bytes", "allocation align")
    )
    for event in MODULE.events:
        event.stacktrace.resolve()
        if isinstance(event, AllocEvent) or isinstance(event, ReallocEvent):
            allocation_size = event.size
            profile_builder.add_event(
                Event(event.stacktrace, [allocation_size, event.align])
            )
    profile_builder.write_file(MODULE.mix_output_name(output_postfix))
