from rsprof.lldbutil import get_function_parameter
from rsprof.traceutil import StackTrace, stacktrace_from_sbframe
from rsprof.tracing import TracingEvent, TracingModule

from lldb import SBFrame, SBBreakpointLocation


MODULE = TracingModule("memtrace")


class MemtraceEvent(TracingEvent):
    def __init__(self, stacktrace: StackTrace) -> None:
        super().__init__(stacktrace)


@MODULE.event
class AllocationEvent(MemtraceEvent):
    def __init__(self, stacktrace: StackTrace, size: int, align: int, addr: int) -> None:
        super().__init__(stacktrace)
        self.size = size
        self.align = align
        self.addr = addr

    def serialize(self):
        return self.base_serialize({"size": self.size, "align": self.align, "addr": self.addr})


@MODULE.event
class DeallocationEvent(MemtraceEvent):
    def __init__(self, stacktrace: StackTrace, size: int, align: int, addr: int) -> None:
        super().__init__(stacktrace)
        self.size = size
        self.align = align
        self.addr = addr

    def serialize(self):
        return self.base_serialize({"size": self.size, "align": self.align, "addr": self.addr})


@MODULE.callback_name("__rsprof_memtrace_event")
def rsprof_memtrace_event(frame: SBFrame, loc: SBBreakpointLocation, extra_args, interal_dict):
    stacktrace = stacktrace_from_sbframe(frame)

    event_id, size, align, ptr = get_function_parameter(
        frame, ("u", "u", "u", "u"))

    if event_id == 0:
        event = AllocationEvent(stacktrace, size, align, ptr)
    else:
        event = DeallocationEvent(stacktrace, size, align, ptr)

    MODULE.append_event(event)


@MODULE.callback_report
def report(prog_module: str):
    return MODULE.serialize(filter_module=prog_module)
