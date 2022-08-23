import struct
from typing import Optional
from rsprof.lldbutil import get_function_parameter
from ..proto import (
    Event,
    ProfileBuilder,
)
from rsprof.traceutil import stacktrace_from_sbframe
from rsprof.tracing import TracingModule

from lldb import SBFrame, SBBreakpointLocation, SBError, SBProcess


MODULE = TracingModule("mutex")


@MODULE.breakpoint_srcloc("sync/mutex.rs", 501)
def mutexguard_create(
    frame: SBFrame, loc: SBBreakpointLocation, extra_args, interal_dict
):
    stacktrace = stacktrace_from_sbframe(frame)
    (mutex_addr,) = get_function_parameter(frame, ("u"))

    print(mutex_addr, "is acquired by thread id", stacktrace.thread_id)


def _inspect_mutexguard(frame: SBFrame, mutexguard_addr: int) -> int:
    process: SBProcess = frame.GetThread().GetProcess()
    error = SBError()
    content = process.ReadMemory(mutexguard_addr, struct.calcsize("P"), error)
    return struct.unpack("P", content)[0]


@MODULE.breakpoint_srcloc("sync/mutex.rs", 525)
def mutexguard_drop(
    frame: SBFrame, loc: SBBreakpointLocation, extra_args, interal_dict
):
    stacktrace = stacktrace_from_sbframe(frame)

    mutex_addr = _inspect_mutexguard(
        frame, get_function_parameter(frame, ("u"))[0])

    print(mutex_addr, "is dropped by thread id", stacktrace.thread_id)
