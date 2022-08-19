from typing import Optional
from rsprof.proto import Event, ProfileBuilder
from rsprof.traceutil import StackTrace, stacktrace_from_sbframe
from rsprof.tracing import TracingEvent, TracingModule

from lldb import SBFrame, SBBreakpointLocation

MODULE = TracingModule("clone")


@MODULE.event
class CloneEvent(TracingEvent):
    def __init__(self, stacktrace: StackTrace) -> None:
        super().__init__(stacktrace)


@MODULE.callback_regex("5clone17h")
def rust_clone(frame: SBFrame, loc: SBBreakpointLocation, _, __):
    stacktrace = stacktrace_from_sbframe(frame)

    MODULE.append_event(CloneEvent(stacktrace))


@MODULE.callback_report
def report(output_postfix: Optional[str]):
    profile_builder = ProfileBuilder(("clone", "count"))
    for event in MODULE.events:
        print(event)
        event.stacktrace.resolve()
        profile_builder.add_event(Event(event.stacktrace, [1]))
    profile_builder.write_file(MODULE.mix_output_name(output_postfix))
