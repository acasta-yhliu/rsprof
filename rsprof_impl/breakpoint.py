from typing import Any, Callable, List, Tuple
from lldb import (
    SBFrame,
    SBBreakpointLocation,
    SBDebugger,
    SBTarget,
    SBBreakpoint,
)
from uuid import uuid1

REGISTERED_BREAKPOINTS: List[
    Tuple[str, int, Callable[[SBFrame, SBBreakpointLocation, Any, Any], None]]
] = []

AT_ENTRANCE = 0
AT_EXIT = 1


def breakpoint_callback(symbol_name: str, breakpoint_location: int):
    def breakpoint_callback_impl(
        callback_func: Callable[[SBFrame, SBBreakpointLocation, Any, Any], None]
    ):
        # register callback
        REGISTERED_BREAKPOINTS.append((symbol_name, breakpoint_location, callback_func))
        return callback_func

    return breakpoint_callback_impl


class BreakpointManager:
    def __init__(self, debugger: SBDebugger, target: SBTarget) -> None:
        self.debugger = debugger
        self.target = target

        # (breakpoint_id, registered_command)
        self.registration: List[int] = []

    def __enter__(self):
        self.target.DisableAllBreakpoints()

        for (symbol_name, breakpoint_location, callback) in REGISTERED_BREAKPOINTS:
            breakpoint: SBBreakpoint = self.target.BreakpointCreateByName(symbol_name)
            print(f"{callback.__module__}.{callback.__qualname__}")
            breakpoint.SetScriptCallbackFunction(
                f"{callback.__module__}.{callback.__qualname__}"
            )
            breakpoint.SetAutoContinue(True)

            self.registration.append(breakpoint.id)

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        for id in self.registration:
            self.target.BreakpointDelete(id)

        self.target.EnableAllBreakpoints()
