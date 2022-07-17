from importlib import import_module
from typing import Any, Callable, Generic, List, TypeVar
from lldb import SBDebugger, SBTarget, SBFrame, SBBreakpointLocation

from rsprof.lldbutil import BreakpointManager
from rsprof.logutil import fail, info, panic, warn

T = TypeVar("T")


class TracingModule(Generic[T]):
    def __init__(self, module_name: str) -> None:
        self.breakpoints = BreakpointManager()
        self.module_name = module_name
        self.events: List[T] = []

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
            warn(f"tracing module '{self.module_name}' is already enabled")
        else:
            if unresolved is not None:
                fail(
                    f"tracing module '{self.module_name}' failed to enable due to unresolved symbol '{unresolved}'"
                )
            else:
                info(f"tracing module '{self.module_name}' is enabled")

    def clear(self):
        self.events.clear()

    def disable(self, target: SBTarget):
        if not self.breakpoints.unset(target):
            warn(f"tracing module '{self.module_name}' is not enabled")
        else:
            info(f"tracing module '{self.module_name}' is disabled")

    def report(self, target: SBTarget):
        if self.is_enabled(target):
            self.reporter()

    def generic_report(self):
        print(f"module '{self.module_name}' recorded {len(self.events)} events")
        for id, event in enumerate(self.events):
            print(f"  {id}. {event}")

    def is_enabled(self, target: SBTarget):
        for t, _ in self.breakpoints.registered_breakpoints:
            if target == t:
                return True
        return False


REGISTED_MODULES = {"memory"}


def load_tracing_modules(debugger: SBDebugger, modules: List[str]):
    if len(modules) == 0:
        modules = list(REGISTED_MODULES)

    for module_name in modules:
        if module_name not in REGISTED_MODULES:
            panic(f"tracing module '{module_name}' does not exist")

    return map(
        lambda x: import_module(f"rsprof.tracing.{x}").MODULE.on_load(debugger), modules
    )
