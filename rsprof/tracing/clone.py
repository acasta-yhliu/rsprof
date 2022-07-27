from rsprof.traceutil import StackTrace, stacktrace_from_sbframe
from rsprof.tracing import TracingEvent, TracingModule

from lldb import SBFrame, SBBreakpointLocation

MODULE = TracingModule("clone")


@MODULE.event
class CloneEvent(TracingEvent):
    def __init__(self, stacktrace: StackTrace) -> None:
        super().__init__(stacktrace)


@MODULE.callback_regex("5clone17h")
def rust_clone(frame: SBFrame, loc:  SBBreakpointLocation, _, __):
    stacktrace = stacktrace_from_sbframe(frame)

    MODULE.append_event(CloneEvent(stacktrace))


@MODULE.callback_report
def report(prog_module: str):
    serialize_event = []
    for event in MODULE.events:
        event.stacktrace.resolve()
        event.stacktrace.filter_module(prog_module)
        serialize_event.append(event.serialize())
    return serialize_event
