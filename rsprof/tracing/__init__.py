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

    def callback_regex(self, regex: str):
        def aux(callback: Callable[[SBFrame, SBBreakpointLocation, Any, Any], None]):
            self.breakpoints.register_callback_regex(regex, callback)
            return callback

        return aux

    def callback_name(self, name: str):
        def aux(callback: Callable[[SBFrame, SBBreakpointLocation, Any, Any], None]):
            self.breakpoints.register_callback_name(name, callback)
            return callback

        return aux

    def callback_report(self, reporter):
        self.reporter = reporter

    def enable(self, target: SBTarget):
        succ_enabled, unresolved = self.breakpoints.set(target)
        if not succ_enabled:
            warn(f"tracing module '{self.name}' is already enabled")
        else:
            if unresolved is not None:
                fail(
                    f"tracing module '{self.name}' failed to enable due to unresolved symbol '{unresolved}'"
                )
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
        for t, _ in self.breakpoints.registered_breakpoints:
            if target == t:
                return True
        return False

    def append_event(self, event):
        self.events.append(event)

    def mix_output_name(self, output_postfix: Optional[str]):
        if output_postfix is None:
            return f"{self.name}.prof"
        else:
            return f"{output_postfix}.{self.name}.prof"


REGISTED_MODULES = {"memory", "clone", "memtrace"}


def load_tracing_modules(debugger: SBDebugger, modules: List[str]):
    if len(modules) == 0:
        modules = list(REGISTED_MODULES)

    for module_name in modules:
        if module_name not in REGISTED_MODULES:
            panic(f"tracing module '{module_name}' does not exist")

    return map(
        lambda x: import_module(f"rsprof.tracing.{x}").MODULE.on_load(debugger), modules
    )


class TracingEvent:
    def __init__(self, stacktrace: StackTrace) -> None:
        self.stacktrace = stacktrace
