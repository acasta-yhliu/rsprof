from typing import List
from rsprof.tracing import TracingModule
from lldb import (
    SBFrame,
    SBBreakpointLocation,
)
from traceutil import stacktrace_from_sbframe, StackTrace
from lldbutil import evaluate_expression_unsigned


class MemoryEvent:
    pass


MODULE: TracingModule[MemoryEvent] = TracingModule("memory")


class AllocEvent(MemoryEvent):
    def __init__(
        self, stacktrace: StackTrace, size: int, align: int, addr: int
    ) -> None:
        self.stacktrace = stacktrace
        self.size = size
        self.align = align
        self.addr = addr

    def __str__(self) -> str:
        return f"alloc {self.size} bytes (align {self.align})"

@MODULE.callback_name("__rust_alloc")
def rust_alloc(frame: SBFrame, loc: SBBreakpointLocation, extra_args, interal_dict):
    stacktrace = stacktrace_from_sbframe(frame)

    # get the size of the allocation
    allocation_size = evaluate_expression_unsigned(frame, "$arg1")
    allocation_align = evaluate_expression_unsigned(frame, "$arg2")

    # TODO: try to fetch the return value, is it possible ?

    MODULE.events.append(AllocEvent(stacktrace, allocation_size, allocation_align, 0))


# currently, there's no need to perform deallocation tracing since we are not tracing
# the entire heap, which, until we get the return value of __rust_alloc
 
# @MODULE.callback_name("__rust_dealloc", "in")
# def rust_dealloc(frame: SBFrame, loc: SBBreakpointLocation, extra_args, interal_dict):
#     pass


@MODULE.callback_report
def report():
    # TODO: better report, with GUI or something else ?
    MODULE.generic_report()
