from typing import List, cast
from rsprof.tracing import TracingModule
from lldb import (
    SBFrame,
    SBBreakpointLocation,
)
from traceutil import stacktrace_from_sbframe, StackTrace
from lldbutil import evaluate_expression_unsigned

MODULE = TracingModule("memory")


class AllocationTrace:
    def __init__(
        self, stacktrace: StackTrace, size: int, align: int, addr: int
    ) -> None:
        self.stacktrace = stacktrace
        self.size = size
        self.align = align
        self.addr = addr


ALLOCATIONS: List[AllocationTrace] = []
DEALLOCATIONS = []


@MODULE.callback_name("__rust_alloc")
def rust_alloc(frame: SBFrame, loc: SBBreakpointLocation, extra_args, interal_dict):
    stacktrace = stacktrace_from_sbframe(frame)

    # get the size of the allocation
    allocation_size = evaluate_expression_unsigned(frame, "$arg1")
    allocation_align = evaluate_expression_unsigned(frame, "$arg2")

    ALLOCATIONS.append(
        AllocationTrace(stacktrace, allocation_size, allocation_align, 0)
    )


# currently, there's no need to perform deallocation tracing since we are not tracing
# the entire heap, which, until we get the return value of __rust_alloc

# @MODULE.callback_name("__rust_dealloc", "in")
# def rust_dealloc(frame: SBFrame, loc: SBBreakpointLocation, extra_args, interal_dict):
#     pass


@MODULE.callback_report
def report():
    print(f"recorded {len(ALLOCATIONS)} allocation events in total")
    for id, allocation in enumerate(ALLOCATIONS):
        print(
            f" {id}. {allocation.size}:align {allocation.align} at thread {allocation.stacktrace.threadid}"
        )
