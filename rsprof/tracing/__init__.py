from importlib import import_module
from typing import Any, Callable, List, Optional, TypeVar
from lldb import SBDebugger, SBTarget, SBFrame, SBBreakpointLocation

from rsprof.lldbutil import BreakpointManager
from rsprof.logutil import fail, info, panic, warn
from rsprof.traceutil import StackTrace

_T = TypeVar("_T")


class TracingModule:
    def __init__(self, name: str) -> None:
        self.breakpoints = BreakpointManager()
        self.name = name
        self.events: List["TracingEvent"] = []

    def on_load(self, debugger: SBDebugger):
        self.breakpoints.update(debugger)
        return self

    def breakpoint_sysregex(self, regex: str):
        def aux(callback: Callable[[SBFrame, SBBreakpointLocation, Any, Any], None]):
            self.breakpoints.br_sysregex(regex, callback)
            return callback

        return aux

    def breakpoint_sysname(self, name: str):
        def aux(callback: Callable[[SBFrame, SBBreakpointLocation, Any, Any], None]):
            self.breakpoints.br_sysname(name, callback)
            return callback

        return aux

    def breakpoint_srcloc(self, file: str, line: int):
        def aux(callback: Callable[[SBFrame, SBBreakpointLocation, Any, Any], None]):
            self.breakpoints.br_srcloc(file, line, callback)
            return callback

        return aux

    def breakpoint_name(self, name: str):
        def aux(callback: Callable[[SBFrame, SBBreakpointLocation, Any, Any], None]):
            self.breakpoints.br_name(name)
            return callback

        return aux

    def breakpoint_regex(self, regex: str):
        def aux(callback: Callable[[SBFrame, SBBreakpointLocation, Any, Any], None]):
            self.breakpoints.br_regex(regex)
            return callback

        return aux

    def register_report_fn(self, reporter):
        self.reporter = reporter

    def enable(self, target: SBTarget):
        result = self.breakpoints.set(target)
        if result == BreakpointManager.DUPLICATE_TARGET:
            warn(f"tracing module '{self.name}' is already enabled")
        elif result == BreakpointManager.HAS_UNRESOLVED:
            warn(f"tracing module '{self.name}' has unresolved breakpoints")
            warn(f"it may not produce desired result")
        else:
            info(f"tracing module '{self.name}' is enabled")

    def clear(self):
        self.events.clear()

    def disable(self, target: SBTarget):
        if not self.breakpoints.unset(target):
            warn(f"tracing module '{self.name}' is not enabled")
        else:
            info(f"tracing module '{self.name}' is disabled")

    def report(self, target: SBTarget, output_postfix: Optional[str]):
        if self.is_enabled(target):
            self.reporter(output_postfix)

    def is_enabled(self, target: SBTarget):
        for reg in self.breakpoints.reg_brs:
            if target == reg.target:
                return True
        return False

    def append_event(self, event):
        self.events.append(event)

    def mix_output_name(self, output_postfix: Optional[str]):
        if output_postfix is None:
            return f"{self.name}.prof"
        else:
            return f"{output_postfix}.{self.name}.prof"


REGISTED_MODULES = {"memory", "mutex", "memtrace"}


def load_tracing_modules(debugger: SBDebugger, modules: List[str]):
    if len(modules) == 0:
        modules = list(REGISTED_MODULES)

    for module_name in modules:
        if module_name not in REGISTED_MODULES:
            panic(f"tracing module '{module_name}' does not exist")

    return map(
        lambda x: import_module(
            f"rsprof.tracing.{x}").MODULE.on_load(debugger), modules
    )


class TracingEvent:
    def __init__(self, stacktrace: StackTrace) -> None:
        self.stacktrace = stacktrace
